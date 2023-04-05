from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.template import loader
from django.utils.translation import gettext_lazy as _
from django.views import View

from libcoveweb2.background_worker import process_supplied_data
from libcoveweb2.celery import CeleryInspector
from libcoveweb2.forms import (
    NewCSVsUploadForm,
    NewJSONTextForm,
    NewJSONUploadForm,
    NewJSONURLForm,
    NewSpreadsheetUploadForm,
)
from libcoveweb2.models import SuppliedData
from libcoveweb2.process.utils import get_tasks

JSON_FORM_CLASSES = {
    "upload_form": NewJSONUploadForm,
    "text_form": NewJSONTextForm,
    "url_form": NewJSONURLForm,
}


def new_json(request):

    forms = {
        form_name: form_class() for form_name, form_class in JSON_FORM_CLASSES.items()
    }
    request_data = None
    if request.POST:
        request_data = request.POST
    if request_data:
        if "paste" in request_data:
            form_name = "text_form"
        elif "url" in request_data:
            form_name = "url_form"
        else:
            form_name = "upload_form"
        forms[form_name] = JSON_FORM_CLASSES[form_name](request_data, request.FILES)
        form = forms[form_name]
        if form.is_valid():
            # Extra Validation
            if form_name == "upload_form":
                if (
                    not request.FILES["file_upload"].content_type
                    in settings.ALLOWED_JSON_CONTENT_TYPES
                ):
                    form.add_error(
                        "file_upload", "This does not appear to be a JSON file"
                    )
                if not [
                    e
                    for e in settings.ALLOWED_JSON_EXTENSIONS
                    if str(request.FILES["file_upload"].name).lower().endswith(e)
                ]:
                    form.add_error(
                        "file_upload", "This does not appear to be a JSON file"
                    )
            elif form_name == "text_form":
                pass  # TODO

            # Process
            if form.is_valid():
                supplied_data = SuppliedData()
                supplied_data.format = "json"
                supplied_data.save()

                if form_name == "upload_form":
                    supplied_data.save_file(request.FILES["file_upload"])
                elif form_name == "text_form":
                    supplied_data.save_file_contents(
                        "input.json",
                        form.cleaned_data["paste"],
                        "application/json",
                        None,
                    )
                elif form_name == "url_form":
                    supplied_data.save_file_from_source_url(
                        form.cleaned_data["url"], content_type="application/json"
                    )

                process_supplied_data(supplied_data.id)
                return HttpResponseRedirect(supplied_data.get_absolute_url())

    return render(request, "libcoveweb2/new_json.html", {"forms": forms})


CSVS_FORM_CLASSES = {
    "upload_form": NewCSVsUploadForm,
}


def new_csvs(request):

    forms = {
        "upload_form": NewCSVsUploadForm(request.POST, request.FILES)
        if request.POST
        else NewCSVsUploadForm()
    }
    form = forms["upload_form"]
    if form.is_valid():
        # Extra Validation
        for field in form.file_field_names:
            if request.FILES.get(field):
                if (
                    not request.FILES[field].content_type
                    in settings.ALLOWED_CSV_CONTENT_TYPES
                ):
                    form.add_error(field, "This does not appear to be a CSV file")
                if not [
                    e
                    for e in settings.ALLOWED_CSV_EXTENSIONS
                    if str(request.FILES[field].name).lower().endswith(e)
                ]:
                    form.add_error(field, "This does not appear to be a CSV file")

        # Process
        if form.is_valid():
            supplied_data = SuppliedData()
            supplied_data.format = "csvs"
            supplied_data.save()

            for field in form.file_field_names:
                if request.FILES.get(field):
                    supplied_data.save_file(request.FILES[field])

            process_supplied_data(supplied_data.id)
            return HttpResponseRedirect(supplied_data.get_absolute_url())

    return render(request, "libcoveweb2/new_csvs.html", {"forms": forms})


SPREADSHEET_FORM_CLASSES = {
    "upload_form": NewSpreadsheetUploadForm,
}


def new_spreadsheet(request):

    forms = {
        "upload_form": NewSpreadsheetUploadForm(request.POST, request.FILES)
        if request.POST
        else NewSpreadsheetUploadForm()
    }
    form = forms["upload_form"]
    if form.is_valid():
        # Extra Validation
        if (
            not request.FILES["file_upload"].content_type
            in settings.ALLOWED_SPREADSHEET_CONTENT_TYPES
        ):
            form.add_error("file_upload", "This does not appear to be a spreadsheet")
        if not [
            e
            for e in settings.ALLOWED_SPREADSHEET_EXTENSIONS
            if str(request.FILES["file_upload"].name).lower().endswith(e)
        ]:
            form.add_error("file_upload", "This does not appear to be a spreadsheet")

        # Process
        if form.is_valid():
            supplied_data = SuppliedData()
            supplied_data.format = "spreadsheet"
            supplied_data.save()

            supplied_data.save_file(request.FILES["file_upload"])

            process_supplied_data(supplied_data.id)
            return HttpResponseRedirect(supplied_data.get_absolute_url())

    return render(request, "libcoveweb2/new_spreadsheet.html", {"forms": forms})


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
        context = self.default_explore_context(supplied_data)

        for task in tasks:
            context.update(task.get_context())

        return self.view_explore(request, context, supplied_data)

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

    def view_being_processed(self, request, supplied_data):
        """Called if the data is currently being processed.  Return a view to show the user."""
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

        return render(request, self.processing_template, context)

    def default_explore_context(self, supplied_data):
        """Called if the data is ready to show to the user. Return a dict of the context to pass to the template."""
        return {}

    def view_explore(self, request, context, supplied_data):
        """Called if the data is ready to show to the user. Return a view to show the user."""
        return render(request, self.explore_template, context)


def handler500(request):
    """500 error handler which includes ``request`` in the context."""

    context = {
        "request": request,
    }
    context.update(settings.COVE_CONFIG)

    t = loader.get_template("libcoveweb2/500.html")
    return HttpResponseServerError(t.render(context))
