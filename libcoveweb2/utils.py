def group_data_list_by(data_list, get_key_function):
    out = {}
    for item in data_list:
        key = get_key_function(item)
        if key not in out:
            out[key] = []
        out[key].append(item)
    return out


def get_file_type(file_name):
    """Takes an filename (type string), and returns a string saying what type it is."""
    # Older versions of this could take DJango objects to.
    # Tho we don't really want to support that, put in a check for that.
    if not isinstance(file_name, str) and hasattr(file_name, "path"):
        file_name = file_name.path
    # First, just check the extension on the file name
    if file_name.lower().endswith(".json"):
        return "json"
    if file_name.lower().endswith(".xlsx"):
        return "xlsx"
    if file_name.lower().endswith(".ods"):
        return "ods"
    if file_name.lower().endswith(".csv"):
        return "csv"
    # Try and load the first bit of the file to see if it's JSON?
    try:
        with open(file_name, "rb") as fp:
            first_byte = fp.read(1)
            if first_byte in [b"{", b"["]:
                return "json"
    except FileNotFoundError:
        pass
    # All right, we give up.
    raise
