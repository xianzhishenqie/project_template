
def diff(dict1, dict2, fields=None):
    """获取字典差异字段。

    :param dict1: 字典1
    :param dict2: 字典2
    :param fields: 比较字段列表
    :return: 差异字典
    """
    fields = fields or dict2.keys()
    ret = {}
    for field in fields:
        if dict1.get(field) != dict2.get(field):
            ret[field] = dict2.get(field)
    return ret


def need_field(field, fields=None):
    """是否需要比较字段

    :param field: 字段
    :param fields: 需要的字段列表
    :return: bool
    """
    if fields is None or field in fields:
        return True

    return False


def filter_data(dict_data, fields=None):
    """过滤字典

    :param dict_data: 字典
    :param fields: 需要的字段列表
    :return: 过滤字典
    """
    if fields is not None:
        exclude_fields = set(dict_data.keys()) - set(fields)
        for field in exclude_fields:
            dict_data.pop(field)

    return dict_data
