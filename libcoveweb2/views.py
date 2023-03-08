from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.template import loader
from django.utils.translation import gettext_lazy as _

from libcoveweb2.forms import (
    NewCSVsUploadForm,
    NewJSONTextForm,
    NewJSONUploadForm,
    NewSpreadsheetUploadForm,
)
from libcoveweb2.models import SuppliedData, SuppliedDataFile

JSON_FORM_CLASSES = {
    "upload_form": NewJSONUploadForm,
    "text_form": NewJSONTextForm,
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

            return HttpResponseRedirect(supplied_data.get_absolute_url())

    return render(request, "libcoveweb2/new_spreadsheet.html", {"forms": forms})


def explore_data_context(request, pk):
    try:
        data = SuppliedData.objects.get(pk=pk)
    except (
        SuppliedData.DoesNotExist,
        ValidationError,
    ):  # Catches primary key does not exist and badly formed UUID
        return (
            {},
            None,
            render(
                request,
                "libcoveweb2/error.html",
                {
                    "sub_title": _(
                        "Sorry, the page you are looking for is not available"
                    ),
                    "link": "index",
                    "link_text": _("Go to Home page"),
                    "msg": _(
                        "We don't seem to be able to find the data you requested."
                    ),
                },
                status=404,
            ),
        )

    if data.expired:
        return (
            {},
            None,
            render(
                request,
                "libcoveweb2/error.html",
                {
                    "sub_title": _(
                        "Sorry, the page you are looking for is not available"
                    ),
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
            ),
        )

    context = {
        "supplied_data_files": SuppliedDataFile.objects.filter(supplied_data=data),
        "created_datetime": data.created.strftime("%A, %d %B %Y %I:%M%p %Z"),
        "created_date": data.created.strftime("%A, %d %B %Y"),
        "created_time": data.created.strftime("%I:%M%p %Z"),
    }

    return (context, data, None)


def handler500(request):
    """500 error handler which includes ``request`` in the context."""

    context = {
        "request": request,
    }
    context.update(settings.COVE_CONFIG)

    t = loader.get_template("libcoveweb2/500.html")
    return HttpResponseServerError(t.render(context))
