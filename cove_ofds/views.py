import json
import logging
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render

from cove_ofds.forms import NewGeoJSONUploadForm
from cove_ofds.process import (
    AdditionalFieldsChecksTask,
    ConvertGeoJSONIntoJSON,
    ConvertJSONIntoGeoJSON,
    ConvertJSONIntoSpreadsheets,
    ConvertSpreadsheetIntoJSON,
    JsonSchemaValidateTask,
    PythonValidateTask,
    WasJSONUploaded,
)
from libcoveweb2.models import SuppliedData
from libcoveweb2.views import explore_data_context

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def index(request):

    return render(request, "cove_ofds/index.html", {})


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
            if (
                not request.FILES[field].content_type
                in settings.ALLOWED_GEOJSON_CONTENT_TYPES
            ):
                form.add_error("file_upload", "This does not appear to be a JSON file")
            if not [
                e
                for e in settings.ALLOWED_GEOJSON_EXTENSIONS
                if str(request.FILES[field].name).lower().endswith(e)
            ]:
                form.add_error("file_upload", "This does not appear to be a JSON file")

        # Process
        if form.is_valid():
            supplied_data = SuppliedData()
            supplied_data.format = "geojson"
            supplied_data.save()

            supplied_data.save_file(
                request.FILES["nodes_file_upload"], meta={"geojson": "nodes"}
            )
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
        try:
            process_data = task.process(process_data)
        except Exception as err:
            print(err)

    # read results
    for task in PROCESS_TASKS:
        try:
            context.update(task.get_context())
        except Exception as err:
            print(err)

    template = "cove_ofds/explore.html"

    return render(request, template, context)
