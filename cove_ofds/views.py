import json
import logging
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render

from cove_ofds.forms import NewGeoJSONUploadForm
from cove_ofds.process import (
    AdditionalFieldsChecksTask,
    ConvertCSVsIntoJSON,
    ConvertGeoJSONIntoJSON,
    ConvertJSONIntoGeoJSON,
    ConvertJSONIntoSpreadsheets,
    ConvertSpreadsheetIntoJSON,
    JsonSchemaValidateTask,
    PythonValidateTask,
    WasJSONUploaded,
)
from libcoveweb2.models import SuppliedData
from libcoveweb2.views import (
    CSVS_FORM_CLASSES,
    JSON_FORM_CLASSES,
    SPREADSHEET_FORM_CLASSES,
    explore_data_context,
)

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


GEOJSON_FORM_CLASSES = {
    "upload_form": NewGeoJSONUploadForm,
}


def index(request):

    forms = {
        "json": {
            form_name: form_class()
            for form_name, form_class in JSON_FORM_CLASSES.items()
        },
        "csvs": {
            form_name: form_class()
            for form_name, form_class in CSVS_FORM_CLASSES.items()
        },
        "geojson": {
            form_name: form_class()
            for form_name, form_class in GEOJSON_FORM_CLASSES.items()
        },
        "spreadsheet": {
            form_name: form_class()
            for form_name, form_class in SPREADSHEET_FORM_CLASSES.items()
        },
    }

    return render(request, "cove_ofds/index.html", {"forms": forms})


def new_geojson(request):

    forms = {
        "upload_form": NewGeoJSONUploadForm(request.POST, request.FILES)
        if request.POST
        else NewGeoJSONUploadForm()
    }
    form = forms["upload_form"]
    if form.is_valid():
        # Extra Validation
        for field in ["nodes_file_upload", "spans_file_upload"]:
            if field in request.FILES:
                if (
                    not request.FILES[field].content_type
                    in settings.ALLOWED_GEOJSON_CONTENT_TYPES
                ):
                    form.add_error(field, "This does not appear to be a JSON file")
                if not [
                    e
                    for e in settings.ALLOWED_GEOJSON_EXTENSIONS
                    if str(request.FILES[field].name).lower().endswith(e)
                ]:
                    form.add_error(field, "This does not appear to be a JSON file")
        if not ("nodes_file_upload" in request.FILES) and not (
            "spans_file_upload" in request.FILES
        ):
            form.add_error("nodes_file_upload", "You must upload nodes or spans")

        # Process
        if form.is_valid():
            supplied_data = SuppliedData()
            supplied_data.format = "geojson"
            supplied_data.save()

            if "nodes_file_upload" in request.FILES:
                supplied_data.save_file(
                    request.FILES["nodes_file_upload"], meta={"geojson": "nodes"}
                )
            if "spans_file_upload" in request.FILES:
                supplied_data.save_file(
                    request.FILES["spans_file_upload"], meta={"geojson": "spans"}
                )

            return HttpResponseRedirect(supplied_data.get_absolute_url())

    return render(request, "cove_ofds/new_geojson.html", {"forms": forms})


def explore_ofds(request, pk):
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error

    PROCESS_TASKS = [
        # Make sure uploads are in primary format
        WasJSONUploaded(db_data),
        ConvertSpreadsheetIntoJSON(db_data),
        ConvertCSVsIntoJSON(db_data),
        ConvertGeoJSONIntoJSON(db_data),
        # Convert into output formats
        ConvertJSONIntoGeoJSON(db_data),
        ConvertJSONIntoSpreadsheets(db_data),
        # Checks and stats
        AdditionalFieldsChecksTask(db_data),
        PythonValidateTask(db_data),
        JsonSchemaValidateTask(db_data),
    ]

    # Process bit that should be a task in a worker
    process_data = {}
    for task in PROCESS_TASKS:
        process_data = task.process(process_data)

    # read results
    for task in PROCESS_TASKS:
        context.update(task.get_context())

    template = "cove_ofds/explore.html"

    return render(request, template, context)
