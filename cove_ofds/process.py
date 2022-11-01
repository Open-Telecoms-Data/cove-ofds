import json
import os.path

from libcove.lib.converters import convert_json, convert_spreadsheet
from libcove.lib.tools import get_file_type as _get_file_type
from libcoveofds.common_checks import common_checks_ofds
from libcoveofds.config import LibCoveOFDSConfig
from libcoveofds.schema import SchemaOFDS
from ofdskit.lib.geojson import JSONToGeoJSONConverter

from libcoveweb2.models import SuppliedDataFile
from libcoveweb2.process import ProcessDataTask


class WasJSONUploaded(ProcessDataTask):
    """Did user upload JSON?
    Then we don't actually have to do anything, but we want to save info about that JSON for later steps."""

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "json":
            return process_data

        supplied_data_json_files = SuppliedDataFile.objects.filter(
            supplied_data=self.supplied_data, content_type="application/json"
        )
        if supplied_data_json_files.count() == 1:
            process_data[
                "json_data_filename"
            ] = supplied_data_json_files.first().upload_dir_and_filename()
        else:
            raise Exception("Can't find JSON original data!")

        return process_data

    def get_context(self):
        return {"original_format": "json"}


class ConvertSpreadsheetIntoJSON(ProcessDataTask):
    """If User uploaded Spreadsheet, convert to our primary format, JSON."""

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "spreadsheet":
            return process_data

        supplied_data_json_files = SuppliedDataFile.objects.filter(
            supplied_data=self.supplied_data
        )
        if supplied_data_json_files.count() == 1:
            input_filename = supplied_data_json_files.first().upload_dir_and_filename()
        else:
            raise Exception("Can't find Spreadsheet original data!")

        config = LibCoveOFDSConfig()
        schema = SchemaOFDS()

        output_dir = os.path.join(self.supplied_data.data_dir(), "unflatten")

        os.makedirs(output_dir, exist_ok=True)

        convert_spreadsheet(
            output_dir,
            os.path.join(self.supplied_data.data_url(), "unflatten"),
            input_filename,
            _get_file_type(input_filename),
            config,
            schema_url=schema.pkg_schema_url,
            replace=True,
        )

        process_data["json_data_filename"] = os.path.join(
            self.supplied_data.data_dir(), "unflatten", "unflattened.json"
        )

        return process_data

    def get_context(self):
        return {"original_format": "spreadsheet"}


class ConvertJSONIntoGeoJSON(ProcessDataTask):
    """Convert primary format (JSON) to GeoJSON"""

    def __init__(self, supplied_data):
        super().__init__(supplied_data)
        self.nodes_file_name = os.path.join(
            self.supplied_data.data_dir(), "nodes.geo.json"
        )
        self.spans_file_name = os.path.join(
            self.supplied_data.data_dir(), "spans.geo.json"
        )

    def process(self, process_data: dict) -> dict:
        # TODO if original format this, don't bother

        if os.path.exists(self.nodes_file_name):
            return

        with open(process_data["json_data_filename"]) as fp:
            data = json.load(fp)

        converter = JSONToGeoJSONConverter()
        converter.process_package(data)

        with open(self.nodes_file_name, "w") as fp:
            json.dump(converter.get_nodes_geojson(), fp, indent=4)

        with open(self.spans_file_name, "w") as fp:
            json.dump(converter.get_spans_geojson(), fp, indent=4)

        return process_data

    def get_context(self):
        context = {}
        # GeoJSON
        if os.path.exists(self.nodes_file_name) and os.path.exists(
            self.spans_file_name
        ):
            context["can_download_geojson"] = True
            context["download_geojson_nodes_url"] = os.path.join(
                self.supplied_data.data_url(), "nodes.geo.json"
            )
            context["download_geojson_spans_url"] = os.path.join(
                self.supplied_data.data_url(), "spans.geo.json"
            )
            context["download_geojson_nodes_size"] = os.stat(
                self.nodes_file_name
            ).st_size
            context["download_geojson_spans_size"] = os.stat(
                self.spans_file_name
            ).st_size
        else:
            context["can_download_geojson"] = False
        # done!
        return context


class ConvertJSONIntoSpreadsheets(ProcessDataTask):
    """Convert primary format (JSON) to spreadsheets"""

    def process(self, process_data: dict) -> dict:

        config = LibCoveOFDSConfig()
        schema = SchemaOFDS()

        output_dir = os.path.join(self.supplied_data.data_dir(), "flatten")

        os.makedirs(output_dir, exist_ok=True)

        convert_json(
            output_dir,
            os.path.join(self.supplied_data.data_url(), "flatten"),
            process_data["json_data_filename"],
            config,
            schema_url=schema.pkg_schema_url,
            replace=True,
            flatten=True,
        )

        return process_data

    def get_context(self):
        context = {}
        # XLSX
        xlsx_filename = os.path.join(
            self.supplied_data.data_dir(), "flatten", "flattened.xlsx"
        )
        if os.path.exists(xlsx_filename):
            context["can_download_xlsx"] = True
            context["download_xlsx_url"] = os.path.join(
                self.supplied_data.data_url(), "flatten", "flattened.xlsx"
            )
            context["download_xlsx_size"] = os.stat(xlsx_filename).st_size
        else:
            context["can_download_xlsx"] = False
        # ODS
        ods_filename = os.path.join(
            self.supplied_data.data_dir(), "flatten", "flattened.ods"
        )
        if os.path.exists(ods_filename):
            context["can_download_ods"] = True
            context["download_ods_url"] = os.path.join(
                self.supplied_data.data_url(), "flatten", "flattened.ods"
            )
            context["download_ods_size"] = os.stat(ods_filename).st_size
        else:
            context["can_download_ods"] = False
        # done!
        return context


class ChecksAndStatistics(ProcessDataTask):
    """With primary format (JSON), run all the checks and statistics."""

    def __init__(self, supplied_data):
        super().__init__(supplied_data)
        self.checks_and_stats_filename = os.path.join(
            self.supplied_data.data_dir(), "checks_and_stats.json"
        )

    def process(self, process_data: dict) -> dict:
        if os.path.exists(self.checks_and_stats_filename):
            return

        with open(process_data["json_data_filename"]) as fp:
            data = json.load(fp)

        config = LibCoveOFDSConfig()
        schema = SchemaOFDS()

        context = common_checks_ofds(
            {"file_type": "json"}, self.supplied_data.data_dir(), data, schema, config
        )

        with open(self.checks_and_stats_filename, "w") as fp:
            json.dump(context, fp, indent=4)

        return process_data

    def get_context(self):
        context = {}
        # checks and stats
        if os.path.exists(self.checks_and_stats_filename):
            with open(self.checks_and_stats_filename) as fp:
                context.update(json.load(fp))
            context["additional_checks_count"] = len(context["additional_checks"])
        # done!
        return context
