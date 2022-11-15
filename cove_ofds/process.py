import json
import os.path
import zipfile

import flattentool
from libcoveofds.additionalfields import AdditionalFields
from libcoveofds.geojson import GeoJSONToJSONConverter, JSONToGeoJSONConverter
from libcoveofds.jsonschemavalidate import JSONSchemaValidator
from libcoveofds.python_validate import PythonValidate
from libcoveofds.schema import OFDSSchema
from sentry_sdk import capture_exception

import cove_ofds.jsonschema_validation_errors
from libcoveweb2.models import SuppliedDataFile
from libcoveweb2.process import ProcessDataTask

# from libcove.lib.converters import convert_json, convert_spreadsheet
from libcoveweb2.utils import get_file_type as _get_file_type
from libcoveweb2.utils import group_data_list_by


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

        # check already done
        # TODO

        supplied_data_json_files = SuppliedDataFile.objects.filter(
            supplied_data=self.supplied_data
        )
        if supplied_data_json_files.count() == 1:
            input_filename = supplied_data_json_files.first().upload_dir_and_filename()
        else:
            raise Exception("Can't find Spreadsheet original data!")

        output_dir = os.path.join(self.supplied_data.data_dir(), "unflatten")

        os.makedirs(output_dir, exist_ok=True)

        schema = OFDSSchema

        unflatten_kwargs = {
            "output_name": os.path.join(output_dir, "unflattened.json"),
            "root_list_path": "networks",
            "input_format": _get_file_type(input_filename),
            "schema": schema.data_schema_url,
        }

        flattentool.unflatten(input_filename, **unflatten_kwargs)

        process_data["json_data_filename"] = os.path.join(
            self.supplied_data.data_dir(), "unflatten", "unflattened.json"
        )

        return process_data

    def get_context(self):
        context = {}
        # original format
        if self.supplied_data.format == "spreadsheet":
            context["original_format"] = "spreadsheet"
            # Download data
            filename = os.path.join(
                self.supplied_data.data_dir(), "unflatten", "unflattened.json"
            )
            if os.path.exists(filename):
                context["can_download_json"] = True
                context["download_json_url"] = os.path.join(
                    self.supplied_data.data_url(), "unflatten", "unflattened.json"
                )
                context["download_json_size"] = os.stat(filename).st_size
            else:
                context["can_download_json"] = False
        # Return
        return context


class ConvertCSVsIntoJSON(ProcessDataTask):
    """If User uploaded CSVs, convert to our primary format, JSON."""

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "csvs":
            return process_data

        # check already done
        # TODO

        output_dir = os.path.join(self.supplied_data.data_dir(), "unflatten")

        os.makedirs(output_dir, exist_ok=True)

        schema = OFDSSchema

        unflatten_kwargs = {
            "output_name": os.path.join(output_dir, "unflattened.json"),
            "root_list_path": "networks",
            "input_format": "csv",
            "schema": schema.data_schema_url,
        }

        flattentool.unflatten(self.supplied_data.upload_dir(), **unflatten_kwargs)

        process_data["json_data_filename"] = os.path.join(
            self.supplied_data.data_dir(), "unflatten", "unflattened.json"
        )

        return process_data

    def get_context(self):
        context = {}
        # original format
        if self.supplied_data.format == "csvs":
            context["original_format"] = "csvs"
            # Download data
            filename = os.path.join(
                self.supplied_data.data_dir(), "unflatten", "unflattened.json"
            )
            if os.path.exists(filename):
                context["can_download_json"] = True
                context["download_json_url"] = os.path.join(
                    self.supplied_data.data_url(), "unflatten", "unflattened.json"
                )
                context["download_json_size"] = os.stat(filename).st_size
            else:
                context["can_download_json"] = False
        # Return
        return context


class ConvertGeoJSONIntoJSON(ProcessDataTask):
    """If User uploaded GeoJSON, convert to our primary format, JSON."""

    def __init__(self, supplied_data):
        super().__init__(supplied_data)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(), "data_from_geojson.json"
        )

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "geojson":
            return process_data

        # check already done
        if os.path.exists(self.data_filename):
            process_data["json_data_filename"] = self.data_filename
            return process_data

        # Get files
        supplied_data_json_files = SuppliedDataFile.objects.filter(
            supplied_data=self.supplied_data
        )
        nodes_data_json_files = [
            f for f in supplied_data_json_files if f.meta.get("geojson") == "nodes"
        ]
        spans_data_json_files = [
            f for f in supplied_data_json_files if f.meta.get("geojson") == "spans"
        ]

        if len(nodes_data_json_files) != 1 and len(spans_data_json_files) != 1:
            raise Exception("Can't find JSON original data!")

        # Get data from files
        # (Or insert dummy data, if no file was uploaded)
        if nodes_data_json_files:
            with open(nodes_data_json_files[0].upload_dir_and_filename()) as fp:
                nodes_data = json.load(fp)
        else:
            nodes_data = {"type": "FeatureCollection", "features": []}
        if spans_data_json_files:
            with open(spans_data_json_files[0].upload_dir_and_filename()) as fp:
                spans_data = json.load(fp)
        else:
            spans_data = {"type": "FeatureCollection", "features": []}

        # Convert
        converter = GeoJSONToJSONConverter()
        converter.process_data(nodes_data, spans_data)

        # Save
        with open(self.data_filename, "w") as fp:
            json.dump(converter.get_json(), fp, indent=4)

        # Info
        process_data["json_data_filename"] = self.data_filename
        return process_data

    def get_context(self):
        # Info
        context = {}
        # original format
        if self.supplied_data.format == "geojson":
            context["original_format"] = "geojson"
            # Download data
            if os.path.exists(self.data_filename):
                context["can_download_json"] = True
                context["download_json_url"] = os.path.join(
                    self.supplied_data.data_url(), "data_from_geojson.json"
                )
                context["download_json_size"] = os.stat(self.data_filename).st_size
            else:
                context["can_download_json"] = False
        # Return
        return context


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
        self.meta_file_name = os.path.join(
            self.supplied_data.data_dir(), "geojson.meta.json"
        )

    def process(self, process_data: dict) -> dict:
        # TODO if original format is geojson, don't bother? or do bother?
        #  because maybe we'll need the meta files for the map?

        if os.path.exists(self.nodes_file_name):
            return process_data

        with open(process_data["json_data_filename"]) as fp:
            data = json.load(fp)

        try:
            converter = JSONToGeoJSONConverter()
            converter.process_package(data)

            with open(self.nodes_file_name, "w") as fp:
                json.dump(converter.get_nodes_geojson(), fp, indent=4)

            with open(self.spans_file_name, "w") as fp:
                json.dump(converter.get_spans_geojson(), fp, indent=4)

            with open(self.meta_file_name, "w") as fp:
                json.dump(converter.get_meta_json(), fp, indent=4)

        except Exception as err:
            capture_exception(err)
            # TODO log and show to user. https://github.com/Open-Telecoms-Data/cove-ofds/issues/24

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
            context["download_geojson_meta_url"] = os.path.join(
                self.supplied_data.data_url(), "geojson.meta.json"
            )
            context["download_geojson_nodes_size"] = os.stat(
                self.nodes_file_name
            ).st_size
            context["download_geojson_spans_size"] = os.stat(
                self.spans_file_name
            ).st_size
            with open(self.meta_file_name) as fp:
                data = json.load(fp)
            context["any_nodes_with_geometry"] = data["any_nodes_with_geometry"]
            context["any_spans_with_geometry"] = data["any_spans_with_geometry"]
        else:
            context["can_download_geojson"] = False
        # done!
        return context


class ConvertJSONIntoSpreadsheets(ProcessDataTask):
    """Convert primary format (JSON) to spreadsheets"""

    def __init__(self, supplied_data):
        super().__init__(supplied_data)
        self.csvs_zip_filename = os.path.join(
            self.supplied_data.data_dir(), "flatten", "flattened.csvs.zip"
        )
        self.output_dir = os.path.join(
            self.supplied_data.data_dir(), "flatten", "flattened"
        )

    def process(self, process_data: dict) -> dict:

        # TODO don't run if already done

        os.makedirs(self.output_dir, exist_ok=True)

        schema = OFDSSchema

        flatten_kwargs = {
            "output_name": self.output_dir,
            "root_list_path": "networks",
            "schema": schema.data_schema_url,
            "truncation_length": 9,
        }

        try:
            flattentool.flatten(process_data["json_data_filename"], **flatten_kwargs)

            # Make Zip file of all CSV files
            with zipfile.ZipFile(self.csvs_zip_filename, "w") as out_zip:
                for f in self._get_list_csv_filenames():
                    out_zip.write(os.path.join(self.output_dir, f), arcname=f)

        except Exception as err:
            capture_exception(err)
            # TODO log and show to user. https://github.com/Open-Telecoms-Data/cove-ofds/issues/24

        return process_data

    def _get_list_csv_filenames(self):
        return sorted(
            [
                f
                for f in os.listdir(self.output_dir)
                if os.path.isfile(os.path.join(self.output_dir, f))
                and f.endswith(".csv")
            ]
        )

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
        # CSVs
        if os.path.exists(self.csvs_zip_filename):
            context["can_download_csvs"] = True
            context["download_csvs_zip_url"] = os.path.join(
                self.supplied_data.data_url(), "flatten", "flattened.csvs.zip"
            )
            context["download_csvs_zip_size"] = os.stat(ods_filename).st_size
            context["download_csv_individual_files"] = [
                {
                    "name": f,
                    "size": os.stat(os.path.join(self.output_dir, f)).st_size,
                    "url": os.path.join(
                        self.supplied_data.data_url(), "flatten", "flattened", f
                    ),
                }
                for f in self._get_list_csv_filenames()
            ]

        else:
            context["can_download_csvs"] = False
        # done!
        return context


class PythonValidateTask(ProcessDataTask):
    def __init__(self, supplied_data):
        super().__init__(supplied_data)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(), "python_validate.json"
        )

    def process(self, process_data: dict) -> dict:
        if os.path.exists(self.data_filename):
            return process_data

        with open(process_data["json_data_filename"]) as fp:
            data = json.load(fp)

        schema = OFDSSchema()
        worker = PythonValidate(schema)
        context = {"additional_checks": worker.validate(data)}

        # has_links_with_external_node_data and has_links_with_external_span_data are shown in a different bit of UI.
        # Set variables and move out of additional_checks
        context["has_links_with_external_node_data"] = (
            True
            if [
                r
                for r in context["additional_checks"]
                if r["type"] == "has_links_with_external_node_data"
            ]
            else False
        )
        context["has_links_with_external_span_data"] = (
            True
            if [
                r
                for r in context["additional_checks"]
                if r["type"] == "has_links_with_external_span_data"
            ]
            else False
        )
        context["additional_checks"] = [
            r
            for r in context["additional_checks"]
            if (
                r["type"] != "has_links_with_external_node_data"
                and r["type"] != "has_links_with_external_span_data"
            )
        ]

        # Count and group what's left
        context["additional_checks_count"] = len(context["additional_checks"])
        context["additional_checks"] = group_data_list_by(
            context["additional_checks"], lambda i: i["type"]
        )

        # The library returns *_name_does_not_match and *_reference_name_set_but_not_in_original as different types,
        # but in this UI we don't care - we just want to show them as one section.
        # So join the 2 types of errors into 1 list.
        for f1, f2 in [
            (
                "node_phase_reference_name_does_not_match",
                "node_phase_reference_name_set_but_not_in_original",
            ),
            (
                "span_phase_reference_name_does_not_match",
                "span_phase_reference_name_set_but_not_in_original",
            ),
            (
                "contract_related_phase_reference_name_does_not_match",
                "contract_related_phase_reference_name_set_but_not_in_original",
            ),
            (
                "node_organisation_reference_name_does_not_match",
                "node_organisation_reference_name_set_but_not_in_original",
            ),
            (
                "span_organisation_reference_name_does_not_match",
                "span_organisation_reference_name_set_but_not_in_original",
            ),
            (
                "phase_organisation_reference_name_does_not_match",
                "phase_organisation_reference_name_set_but_not_in_original",
            ),
        ]:
            new_list = context["additional_checks"].get(f1, []) + context[
                "additional_checks"
            ].get(f2, [])
            if new_list:
                context["additional_checks"][f1] = new_list

        # Work out which level to show box at
        error_level_checks = [
            "span_start_node_not_found",
            "span_end_node_not_found",
            "node_location_type_incorrect",
            "node_location_coordinates_incorrect",
            "span_route_type_incorrect",
            "span_route_coordinates_incorrect",
            "node_phase_reference_id_not_found",
            "span_phase_reference_id_not_found",
            "contract_related_phase_reference_id_not_found",
            "node_phase_reference_name_does_not_match",
            "span_phase_reference_name_does_not_match",
            "contract_related_phase_reference_name_does_not_match",
            "node_phase_reference_name_set_but_not_in_original",
            "span_phase_reference_name_set_but_not_in_original",
            "contract_related_phase_reference_name_set_but_not_in_original",
            "node_organisation_reference_id_not_found",
            "span_organisation_reference_id_not_found",
            "phase_organisation_reference_id_not_found",
            "node_organisation_reference_name_does_not_match",
            "span_organisation_reference_name_does_not_match",
            "phase_organisation_reference_name_does_not_match",
            "node_organisation_reference_name_set_but_not_in_original",
            "span_organisation_reference_name_set_but_not_in_original",
            "phase_organisation_reference_name_set_but_not_in_original",
            "node_international_connections_country_not_set",
        ]
        if [i for i in error_level_checks if i in context["additional_checks"].keys()]:
            context["additional_checks_level"] = "Error"
        elif "node_not_used_in_any_spans" in context["additional_checks"].keys():
            context["additional_checks_level"] = "Warning"
        else:
            context["additional_checks_level"] = "n/a"

        with open(self.data_filename, "w") as fp:
            json.dump(context, fp, indent=4)

        return process_data

    def get_context(self):
        context = {}
        # data
        if os.path.exists(self.data_filename):
            with open(self.data_filename) as fp:
                context.update(json.load(fp))
        # done!
        return context


class JsonSchemaValidateTask(ProcessDataTask):
    def __init__(self, supplied_data):
        super().__init__(supplied_data)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(), "jsonschema_validate.json"
        )

    def process(self, process_data: dict) -> dict:
        if os.path.exists(self.data_filename):
            return process_data

        with open(process_data["json_data_filename"]) as fp:
            data = json.load(fp)

        schema = OFDSSchema()
        worker = JSONSchemaValidator(schema)

        # Get list of validation errors
        validation_errors = worker.validate(data)
        validation_errors = [i.json() for i in validation_errors]

        # Add type to each
        validation_errors = [
            cove_ofds.jsonschema_validation_errors.add_type_to_json_schema_validation_error(
                i
            )
            for i in validation_errors
        ]

        # Add count
        context = {"validation_errors_count": len(validation_errors)}

        # group by type
        validation_errors = group_data_list_by(
            validation_errors, lambda i: str(i["cove_type"])
        )

        # and we are done
        context["validation_errors"] = validation_errors

        with open(self.data_filename, "w") as fp:
            json.dump(context, fp, indent=4)

        return process_data

    def get_context(self):
        context = {}
        # data
        if os.path.exists(self.data_filename):
            with open(self.data_filename) as fp:
                context.update(json.load(fp))
        # done!
        return context


class AdditionalFieldsChecksTask(ProcessDataTask):
    def __init__(self, supplied_data):
        super().__init__(supplied_data)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(), "additional_fields.json"
        )

    def process(self, process_data: dict) -> dict:
        if os.path.exists(self.data_filename):
            return process_data

        with open(process_data["json_data_filename"]) as fp:
            data = json.load(fp)

        schema = OFDSSchema()
        worker = AdditionalFields(schema)

        context = {"additional_fields": worker.process(data)}
        context["additional_fields_count"] = len(context["additional_fields"])

        with open(self.data_filename, "w") as fp:
            json.dump(context, fp, indent=4)

        return process_data

    def get_context(self):
        context = {}
        # data
        if os.path.exists(self.data_filename):
            with open(self.data_filename) as fp:
                context.update(json.load(fp))
        # done!
        return context
