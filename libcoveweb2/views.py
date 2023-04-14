from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponseServerError, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.utils.translation import gettext_lazy as _
from django.views import View

from libcoveweb2.background_worker import process_supplied_data
from libcoveweb2.celery import CeleryInspector
from libcoveweb2.models import SuppliedData
from libcoveweb2.process.utils import get_tasks


class InputDataView(View):
    form_classes = None
    input_template = None
    allowed_content_types = None
    content_type_incorrect_message = "This file is not the correct type."
    allowed_file_extensions = None
    file_extension_incorrect_message = "This file is not the correct type."
    supplied_data_format = None

    def get_active_form_key(self, forms, request_data):
        return None

    def get_file_field_names_in_form(self, form):
        return form.file_field_names

    def save_file_content_to_supplied_data(
        self, form_name, form, request, supplied_data
    ):
        pass

    def get(self, request):
        forms = {
            form_name: form_class()
            for form_name, form_class in self.form_classes.items()
        }
        return render(request, self.input_template, {"forms": forms})

    def post(self, request):
        forms = {
            form_name: form_class()
            for form_name, form_class in self.form_classes.items()
        }
        request_data = None
        if request.POST:
            request_data = request.POST
        if request_data:
            form_name = self.get_active_form_key(forms, request_data)
            if form_name:
                forms[form_name] = self.form_classes[form_name](
                    request_data, request.FILES
                )
                form = forms[form_name]
                # Extra validation
                self.validate_content_type_and_file_extensions(form_name, form, request)

                # If fine, save
                if form.is_valid():
                    supplied_data = SuppliedData()
                    supplied_data.format = self.supplied_data_format
                    supplied_data.save()
                    self.save_file_content_to_supplied_data(
                        form_name, form, request, supplied_data
                    )
                    process_supplied_data(supplied_data.id)
                    return HttpResponseRedirect(supplied_data.get_absolute_url())

        return render(request, self.input_template, {"forms": forms})

    def validate_content_type_and_file_extensions(self, form_name, form, request):
        for field in self.get_file_field_names_in_form(form):
            if request.FILES.get(field):
                if self.allowed_content_types and (
                    not request.FILES[field].content_type in self.allowed_content_types
                ):
                    form.add_error(field, self.content_type_incorrect_message)
                if self.allowed_file_extensions and not [
                    e
                    for e in self.allowed_file_extensions
                    if str(request.FILES[field].name).lower().endswith(e)
                ]:
                    form.add_error(field, self.file_extension_incorrect_message)


class ExploreDataView(View):
    """View for data explore page.

    This is broken into variables/functions so that it can be extended by the cove app
    and specific bits overwritten as needed.
    """

    error_template = "libcoveweb2/error.html"
    explore_template = None
    processing_template = "libcoveweb2/processing.html"

    def get(self, request, pk):
        """Main processing. Not intended to be overridden."""
        # Does data exist at all?
        try:
            supplied_data: SuppliedData = SuppliedData.objects.get(pk=pk)
        except (
            SuppliedData.DoesNotExist,
            ValidationError,
        ):  # Catches primary key does not exist and badly formed UUID
            return self.view_does_not_exist(request)

        # Is data in error
        if supplied_data.error:
            return self.view_data_has_error(request, supplied_data)

        # Is data Expired?
        if supplied_data.expired:
            return self.view_has_expired(request, supplied_data)

        # Is data still to be processed?
        if not supplied_data.processed:
            return self.view_being_processed(request, supplied_data)

        # Get tasks
        tasks = get_tasks(supplied_data)

        # Is data processed but needs to be reprocessed?
        for task in tasks:
            if task.is_processing_applicable() and task.is_processing_needed():
                supplied_data.processed = None
                supplied_data.save()
                process_supplied_data(supplied_data.id)
                return self.view_being_processed(request, supplied_data)

        # Data is there and we can show it!
        return self.view_explore(request, tasks, supplied_data)

    def view_does_not_exist(self, request):
        """Called if the data does not exist at all. Return a view to show the user."""
        return render(
            request,
            self.error_template,
            {
                "sub_title": _("Sorry, the page you are looking for is not available"),
                "link": "index",
                "link_text": _("Go to Home page"),
                "msg": _("We don't seem to be able to find the data you requested."),
            },
            status=404,
        )

    def view_data_has_error(self, request, supplied_data):
        """Called if the supplied data has any error set."""
        return render(
            request,
            self.error_template,
            {
                "sub_title": _("Sorry, there was an error."),
                "link": "index",
                "link_text": _("Go to Home page"),
                "msg": _("There was an error."),
            },
            status=500,
        )

    def view_has_expired(self, request, supplied_data):
        """Called if the data has expired and has now been deleted. Return a view to show the user."""
        return render(
            request,
            self.error_template,
            {
                "sub_title": _("Sorry, the page you are looking for is not available"),
                "link": "index",
                "link_text": _("Go to Home page"),
                # TODO replace 7 below with value from settings
                "msg": _(
                    "The data you were hoping to explore no longer exists.\n\nThis is because all "
                    "data supplied to this website is automatically deleted after 7 days, and therefore "
                    "the analysis of that data is no longer available."
                ),
            },
            status=404,
        )

    def get_being_processed_context(self, request, supplied_data) -> dict:
        """Return python dict of context to use for being processed view."""
        context = {}
        celery_inspector = CeleryInspector()

        if celery_inspector.is_supplied_data_being_processed(supplied_data.id):
            context["state"] = "processing"
            tasks = get_tasks(supplied_data)
            count_tasks = 0
            count_tasks_to_do = 0
            for task in tasks:
                if task.is_processing_applicable():
                    count_tasks += 1
                    if task.is_processing_needed():
                        count_tasks_to_do += 1
            context["count_tasks"] = count_tasks
            context["count_tasks_to_do"] = count_tasks_to_do
            context["count_tasks_done"] = count_tasks - count_tasks_to_do
        else:
            context["state"] = "waiting"
        return context

    def view_being_processed(self, request, supplied_data):
        """Called if the data is currently being processed.  Return a view to show the user."""
        return render(
            request,
            self.processing_template,
            self.get_being_processed_context(request, supplied_data),
        )

    def default_explore_context(self, supplied_data) -> dict:
        """Called if the data is ready to show to the user. Return a dict of the context to pass to the template."""
        return {}

    def get_explore_context(self, request, tasks, supplied_data) -> dict:
        """Return python dict of context to use for explore view."""
        context = self.default_explore_context(supplied_data)
        for task in tasks:
            context.update(task.get_context())
        return context

    def view_explore(self, request, tasks, supplied_data):
        """Called if the data is ready to show to the user. Return a view to show the user."""
        return render(
            request,
            self.explore_template,
            self.get_explore_context(request, tasks, supplied_data),
        )


class ExploreDataProcessingStatusAPIView(ExploreDataView):
    def view_does_not_exist(self, request):
        return JsonResponse({"error": "Does not exist"}, status=404)

    def view_data_has_error(self, request, supplied_data):
        return JsonResponse({"error": "Data has error"}, status=500)

    def view_has_expired(self, request, supplied_data):
        return JsonResponse({"error": "Data has expired"}, status=500)

    def view_being_processed(self, request, supplied_data):
        return JsonResponse(
            self.get_being_processed_context(request, supplied_data), status=200
        )

    def view_explore(self, request, context, supplied_data):
        return JsonResponse({"state": "ready"}, status=200)


def handler500(request):
    """500 error handler which includes ``request`` in the context."""

    context = {
        "request": request,
    }
    context.update(settings.COVE_CONFIG)

    t = loader.get_template("libcoveweb2/500.html")
    return HttpResponseServerError(t.render(context))
