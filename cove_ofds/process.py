import json
import os.path
import zipfile

import flattentool
from libcoveofds.additionalfields import AdditionalFields
from libcoveofds.geojson import (
    GeoJSONAssumeFeatureType,
    GeoJSONToJSONConverter,
    JSONToGeoJSONConverter,
)
from libcoveofds.jsonschemavalidate import JSONSchemaValidator
from libcoveofds.python_validate import PythonValidate
from libcoveofds.schema import OFDSSchema
from sentry_sdk import capture_exception

import cove_ofds.jsonschema_validation_errors
from libcoveweb2.process.base import ProcessDataTask
from libcoveweb2.process.common_tasks.task_with_state import TaskWithState

# from libcove.lib.converters import convert_json, convert_spreadsheet
from libcoveweb2.utils import get_file_type_for_flatten_tool, group_data_list_by


class WasJSONUploaded(ProcessDataTask):
    """Did user upload JSON?
    Then we don't actually have to do anything, but we want to save info about that JSON for later steps."""

    def is_processing_applicable(self) -> bool:
        return True

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "json":
            return process_data

        supplied_data_json_files = [
            i for i in self.supplied_data_files if i.content_type == "application/json"
        ]
        if len(supplied_data_json_files) == 1:
            process_data["json_data_filename"] = supplied_data_json_files[
                0
            ].upload_dir_and_filename()
        else:
            raise Exception("Can't find JSON original data!")

        return process_data

    def get_context(self):
        return {"original_format": "json"}


CONVERT_SPREADSHEET_INTO_JSON_DIR_NAME = "unflatten"


class ConvertSpreadsheetIntoJSON(ProcessDataTask):
    """If User uploaded Spreadsheet, convert to our primary format, JSON."""

    def __init__(self, supplied_data, supplied_data_files):
        super().__init__(supplied_data, supplied_data_files)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_SPREADSHEET_INTO_JSON_DIR_NAME,
            "unflattened.json",
        )

    def is_processing_applicable(self) -> bool:
        return self.supplied_data.format == "spreadsheet"

    def is_processing_needed(self) -> bool:
        return self.supplied_data.format == "spreadsheet" and not os.path.exists(
            self.data_filename
        )

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "spreadsheet":
            return process_data

        process_data["json_data_filename"] = self.data_filename

        # check already done
        if os.path.exists(self.data_filename):
            return process_data

        if len(self.supplied_data_files) != 1:
            raise Exception("Can't find Spreadsheet original data!")

        input_filename = self.supplied_data_files[0].upload_dir_and_filename()

        output_dir = os.path.join(
            self.supplied_data.data_dir(), CONVERT_SPREADSHEET_INTO_JSON_DIR_NAME
        )

        os.makedirs(output_dir, exist_ok=True)

        schema = OFDSSchema

        unflatten_kwargs = {
            "output_name": os.path.join(output_dir, "unflattened.json"),
            "root_list_path": "networks",
            "input_format": get_file_type_for_flatten_tool(self.supplied_data_files[0]),
            "schema": schema.network_schema_url,
            "convert_wkt": True,
        }

        flattentool.unflatten(input_filename, **unflatten_kwargs)

        return process_data

    def get_context(self):
        context = {}
        # original format
        if self.supplied_data.format == "spreadsheet":
            context["original_format"] = "spreadsheet"
            # Download data
            if os.path.exists(self.data_filename):
                context["can_download_json"] = True
                context["download_json_url"] = os.path.join(
                    self.supplied_data.data_url(),
                    CONVERT_SPREADSHEET_INTO_JSON_DIR_NAME,
                    "unflattened.json",
                )
                context["download_json_size"] = os.stat(self.data_filename).st_size
            else:
                context["can_download_json"] = False
        # Return
        return context


CONVERT_CSVS_INTO_JSON_DIR_NAME = "unflatten"


class ConvertCSVsIntoJSON(ProcessDataTask):
    """If User uploaded CSVs, convert to our primary format, JSON."""

    def __init__(self, supplied_data, supplied_data_files):
        super().__init__(supplied_data, supplied_data_files)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_CSVS_INTO_JSON_DIR_NAME,
            "unflattened.json",
        )

    def is_processing_applicable(self) -> bool:
        return self.supplied_data.format == "csvs"

    def is_processing_needed(self) -> bool:
        return self.supplied_data.format == "csvs" and not os.path.exists(
            self.data_filename
        )

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "csvs":
            return process_data

        process_data["json_data_filename"] = self.data_filename

        # check already done
        if os.path.exists(self.data_filename):
            return process_data

        output_dir = os.path.join(
            self.supplied_data.data_dir(), CONVERT_CSVS_INTO_JSON_DIR_NAME
        )

        os.makedirs(output_dir, exist_ok=True)

        schema = OFDSSchema

        unflatten_kwargs = {
            "output_name": os.path.join(output_dir, "unflattened.json"),
            "root_list_path": "networks",
            "input_format": "csv",
            "schema": schema.package_schema_url,
            "convert_wkt": True,
        }

        flattentool.unflatten(self.supplied_data.upload_dir(), **unflatten_kwargs)

        return process_data

    def get_context(self):
        context = {}
        # original format
        if self.supplied_data.format == "csvs":
            context["original_format"] = "csvs"
            # Download data
            if os.path.exists(self.data_filename):
                context["can_download_json"] = True
                context["download_json_url"] = os.path.join(
                    self.supplied_data.data_url(),
                    CONVERT_CSVS_INTO_JSON_DIR_NAME,
                    "unflattened.json",
                )
                context["download_json_size"] = os.stat(self.data_filename).st_size
            else:
                context["can_download_json"] = False
        # Return
        return context


class ConvertGeoJSONIntoJSON(ProcessDataTask):
    """If User uploaded GeoJSON, convert to our primary format, JSON."""

    def __init__(self, supplied_data, supplied_data_files):
        super().__init__(supplied_data, supplied_data_files)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(), "data_from_geojson.json"
        )

    def is_processing_applicable(self) -> bool:
        return self.supplied_data.format == "geojson"

    def is_processing_needed(self) -> bool:
        return self.supplied_data.format == "geojson" and not os.path.exists(
            self.data_filename
        )

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "geojson":
            return process_data

        # check already done
        if os.path.exists(self.data_filename):
            process_data["json_data_filename"] = self.data_filename
            return process_data

        # Get files
        nodes_data_json_files = [
            f for f in self.supplied_data_files if f.meta.get("geojson") == "nodes"
        ]
        spans_data_json_files = [
            f for f in self.supplied_data_files if f.meta.get("geojson") == "spans"
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
        converter.process_data(
            nodes_data, assumed_feature_type=GeoJSONAssumeFeatureType.NODE
        )
        converter.process_data(
            spans_data, assumed_feature_type=GeoJSONAssumeFeatureType.SPAN
        )

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

    nodeFields = {
        "/features/properties/network/name": "Network",
        "/features/properties/phase/name": "Phase",
        "/features/properties/physicalInfrastructureProvider/name": "Physical Infrastructure Provider",
        "/features/properties/networkProviders/name": "Network Providers",
        "/features/properties/technologies": "Technologies",
        "/features/properties/status": "Status",
        "/features/properties/type": "Type",
        "/features/properties/accessPoint": "accessPoint",
        "/features/properties/power": "Power",
    }

    spanFields = {
        "/features/properties/network/name": "Network",
        "/features/properties/phase/name": "Phase",
        "/features/properties/physicalInfrastructureProvider/name": "Physical Infrastructure Provider",
        "/features/properties/networkProviders/name": "Network Providers",
        "/features/properties/supplier/name": "Supplier",
        "/features/properties/transmissionMedium": "Transmission Medium",
        "/features/properties/status": "Status",
        "/features/properties/deployment": "Deployment",
        "/features/properties/darkFibre": "Dark Fibre",
        "/features/properties/fibreType": "Fibre Type",
        "/features/properties/fibreCount": "Fibre Count",
        "/features/properties/technologies": "Technologies",
        "/features/properties/capacity": "Capacity",
    }

    def __init__(self, supplied_data, supplied_data_files):
        super().__init__(supplied_data, supplied_data_files)
        self.nodes_file_name = os.path.join(
            self.supplied_data.data_dir(), "nodes.geo.json"
        )
        self.spans_file_name = os.path.join(
            self.supplied_data.data_dir(), "spans.geo.json"
        )
        self.meta_file_name = os.path.join(
            self.supplied_data.data_dir(), "geojson.meta.json"
        )

    def is_processing_applicable(self) -> bool:
        return True

    def is_processing_needed(self) -> bool:
        return not os.path.exists(self.nodes_file_name)

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
            context["nodes_fields"] = {
                field.split("/")[3]: label
                for field, label in self.nodeFields.items()
                if field in data["nodes_output_field_coverage"]
            }
            context["spans_fields"] = {
                field.split("/")[3]: label
                for field, label in self.spanFields.items()
                if field in data["spans_output_field_coverage"]
            }
        else:
            context["can_download_geojson"] = False
        # done!
        return context


CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME = "flatten"


class ConvertJSONIntoSpreadsheets(ProcessDataTask):
    """Convert primary format (JSON) to spreadsheets"""

    def __init__(self, supplied_data, supplied_data_files):
        super().__init__(supplied_data, supplied_data_files)
        self.csvs_zip_filename = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
            "flattened.csvs.zip",
        )
        self.output_dir = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
            "data",
        )
        self.xlsx_filename = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
            "data.xlsx",
        )

    def is_processing_applicable(self) -> bool:
        return True

    def is_processing_needed(self) -> bool:
        return not os.path.exists(self.xlsx_filename)

    def process(self, process_data: dict) -> dict:

        # don't run if already done
        if os.path.exists(self.xlsx_filename):
            return process_data

        os.makedirs(self.output_dir, exist_ok=True)

        schema = OFDSSchema

        flatten_kwargs = {
            "output_name": self.output_dir,
            "root_list_path": "networks",
            "schema": schema.network_schema_url,
            "truncation_length": 9,
            "main_sheet_name": "networks",
            "convert_wkt": True,
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
        if os.path.exists(self.xlsx_filename):
            context["can_download_xlsx"] = True
            context["download_xlsx_url"] = os.path.join(
                self.supplied_data.data_url(),
                CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
                "data.xlsx",
            )
            context["download_xlsx_size"] = os.stat(self.xlsx_filename).st_size
        else:
            context["can_download_xlsx"] = False
        # ODS
        ods_filename = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
            "data.ods",
        )
        if os.path.exists(ods_filename):
            context["can_download_ods"] = True
            context["download_ods_url"] = os.path.join(
                self.supplied_data.data_url(),
                CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
                "data.ods",
            )
            context["download_ods_size"] = os.stat(ods_filename).st_size
        else:
            context["can_download_ods"] = False
        # CSVs
        if os.path.exists(self.csvs_zip_filename):
            context["can_download_csvs"] = True
            context["download_csvs_zip_url"] = os.path.join(
                self.supplied_data.data_url(),
                CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
                "flattened.csvs.zip",
            )
            context["download_csvs_zip_size"] = os.stat(self.csvs_zip_filename).st_size
            context["download_csv_individual_files"] = [
                {
                    "name": f,
                    "size": os.stat(os.path.join(self.output_dir, f)).st_size,
                    "url": os.path.join(
                        self.supplied_data.data_url(), "flatten", "data", f
                    ),
                }
                for f in self._get_list_csv_filenames()
            ]

        else:
            context["can_download_csvs"] = False
        # done!
        return context


class PythonValidateTask(TaskWithState):

    state_filename: str = "python_validate.py"

    def process_get_state(self, process_data: dict):

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

        return context, process_data


class JsonSchemaValidateTask(TaskWithState):

    state_filename: str = "jsonschema_validate.py"

    def process_get_state(self, process_data: dict):

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

        return context, process_data


class AdditionalFieldsChecksTask(TaskWithState):

    state_filename: str = "additional_fields_2.py"

    def process_get_state(self, process_data: dict):

        with open(process_data["json_data_filename"]) as fp:
            data = json.load(fp)

        schema = OFDSSchema()
        worker = AdditionalFields(schema)

        output = worker.process(data)
        context = {"additional_fields": output}
        context["any_additional_fields_exist"] = len(output) > 0

        return context, process_data
