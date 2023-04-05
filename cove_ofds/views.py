import json
import logging
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render

from cove_ofds.forms import NewGeoJSONUploadForm, NewGeoJSONURLForm
from libcoveweb2.background_worker import process_supplied_data
from libcoveweb2.models import SuppliedData, SuppliedDataFile
from libcoveweb2.views import (
    CSVS_FORM_CLASSES,
    JSON_FORM_CLASSES,
    SPREADSHEET_FORM_CLASSES,
    ExploreDataView,
)

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


GEOJSON_FORM_CLASSES = {
    "upload_form": NewGeoJSONUploadForm,
    "url_form": NewGeoJSONURLForm,
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
        form_name: form_class()
        for form_name, form_class in GEOJSON_FORM_CLASSES.items()
    }
    request_data = None
    if request.POST:
        request_data = request.POST
    if request_data and (
        "nodes_file_url" in request_data or "spans_file_url" in request_data
    ):
        form_name = "url_form"
    else:
        form_name = "upload_form"
    forms[form_name] = GEOJSON_FORM_CLASSES[form_name](request_data, request.FILES)
    form = forms[form_name]
    if form.is_valid():
        # Extra Validation For Upload
        if form_name == "upload_form":
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
        # Extra Validation For URL
        # Should check at least one URL passed, but I think that's essentially done by the form_name selector above

        # Process
        if form.is_valid():
            supplied_data = SuppliedData()
            supplied_data.format = "geojson"
            supplied_data.save()

            if form_name == "upload_form":
                if "nodes_file_upload" in request.FILES:
                    supplied_data.save_file(
                        request.FILES["nodes_file_upload"], meta={"geojson": "nodes"}
                    )
                if "spans_file_upload" in request.FILES:
                    supplied_data.save_file(
                        request.FILES["spans_file_upload"], meta={"geojson": "spans"}
                    )
            if form_name == "url_form":
                if "nodes_file_url" in form.cleaned_data:
                    supplied_data.save_file_from_source_url(
                        form.cleaned_data["nodes_file_url"],
                        meta={"geojson": "nodes"},
                        content_type="application/json",
                    )
                if "spans_file_url" in form.cleaned_data:
                    supplied_data.save_file_from_source_url(
                        form.cleaned_data["spans_file_url"],
                        meta={"geojson": "spans"},
                        content_type="application/json",
                    )

            process_supplied_data(supplied_data.id)
            return HttpResponseRedirect(supplied_data.get_absolute_url())
    return render(request, "cove_ofds/new_geojson.html", {"forms": forms})


class ExploreOFDSView(ExploreDataView):
    explore_template = "cove_ofds/explore.html"

    def default_explore_context(self, supplied_data):
        return {
            # Currently hard coded because the library only supports this version,
            # but in future this should come from one of the process tasks
            "schema_version_used": "0.2",
            # Misc
            "supplied_data_files": SuppliedDataFile.objects.filter(
                supplied_data=supplied_data
            ),
            "created_datetime": supplied_data.created.strftime(
                "%A, %d %B %Y %I:%M%p %Z"
            ),
            "created_date": supplied_data.created.strftime("%A, %d %B %Y"),
            "created_time": supplied_data.created.strftime("%I:%M%p %Z"),
        }
