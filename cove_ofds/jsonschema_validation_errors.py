# This function may be a candidate to move to libcoveofds?
# It could do with some testing, wherever it ends up
def add_type_to_json_schema_validation_error(data: dict) -> dict:

    if data["validator"] == "const":
        data["cove_type"] = "Valuedoesnotmatchconstant"

    elif data["validator"] == "minItems":
        data["cove_type"] = "Emptyarray"

    elif data["validator"] == "uniqueItems":
        data["cove_type"] = "Nonuniqueitems"

    # these 2 pattern checks are brittle
    # using instance is not a great choice as that may easily change if the schema changes. TODO
    elif data["validator"] == "pattern" and data["instance"] in [
        "properties",
        "features",
    ]:
        data["cove_type"] = "Fieldnamedoesnotmatchpattern"

    elif data["validator"] == "pattern" and data["instance"] == "describedby":
        data["cove_type"] = "Valuedoesnotmatchpattern"

    elif data["validator"] == "minLength":
        data["cove_type"] = "Emptystring"

    elif data["validator"] == "enum":
        data["cove_type"] = "Valuedoesnotmatchanycodes"

    elif data["validator"] == "type" and data["validator_value"] == "boolean":
        data["cove_type"] = "Valueisnotaboolean"

    elif data["validator"] == "type" and data["validator_value"] == "integer":
        data["cove_type"] = "Valueisnotaninteger"

    elif data["validator"] == "type" and data["validator_value"] == "number":
        data["cove_type"] = "Valueisnotanumber"

    elif data["validator"] == "type" and data["validator_value"] == "string":
        data["cove_type"] = "Valueisnotastring"

    elif data["validator"] == "type" and data["validator_value"] == "object":
        data["cove_type"] = "Valueisnotanobject"

    elif data["validator"] == "type" and data["validator_value"] == "array":
        data["cove_type"] = "Valueisnotanarray"

    elif data["validator"] == "required":
        # Need to get Id field - https://github.com/Open-Telecoms-Data/cove-ofds/issues/70
        if data["message"].endswith("' is a required property"):
            message_bits = data["message"].split("'")
            data["validator_value"] = message_bits[1]
        data["cove_type"] = "Missingrequiredfields"

    elif data["validator"] == "minProperties":
        data["cove_type"] = "Emptyobject"

    elif data["validator"] == "additionalProperties":
        data["cove_type"] = "Additionalproperties"

    elif data["validator"] == "format" and data["validator_value"] == "date":
        data["cove_type"] = "Incorrectlyformatteddate"

    elif data["validator"] == "format" and data["validator_value"] == "iri":
        data["cove_type"] = "Incorrectlyformattediri"

    elif data["validator"] == "format" and data["validator_value"] == "uri":
        data["cove_type"] = "Incorrectlyformatteduri"

    elif data["validator"] == "format" and data["validator_value"] == "uuid":
        data["cove_type"] = "Incorrectlyformatteduuid"

    else:
        data["cove_type"] = "unknown"

    # TODO this should be in libcoveofds
    data["path_no_num"] = tuple(key for key in data["path"] if isinstance(key, str))

    return data
