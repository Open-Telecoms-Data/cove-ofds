def group_data_list_by(data_list, get_key_function):
    out = {}
    for item in data_list:
        key = get_key_function(item)
        if not key in out:
            out[key] = []
        out[key].append(item)
    return out
