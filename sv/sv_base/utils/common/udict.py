
def diff(dict1, dict2, fields=None):
    fields = fields or dict2.keys()
    ret = {}
    for field in fields:
        if dict1.get(field) != dict2.get(field):
            ret[field] = dict2.get(field)
    return ret


def need_field(field, fields=None):
    if fields is None or field in fields:
        return True

    return False


def filter_data(dict_data, fields=None):
    if fields is not None:
        exclude_fields = set(dict_data.keys()) - set(fields)
        for field in exclude_fields:
            dict_data.pop(field)

    return dict_data
