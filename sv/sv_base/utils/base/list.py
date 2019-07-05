
def convert_item(type_class, item):
    """对元素进行类型强制转换

    :param type_class: 类型
    :param item: 元素
    :return: 转换值
    """
    return type_class(item)


def type_filter(items, type_class, strict=False):
    """过滤转换指定类型的元素列表

    :param items: 元素列表
    :param type_class: 类型
    :param strict: 严格模式（转换失败抛出异常）
    :return: 过滤结果
    """
    converted_items = []
    for item in items:
        if item is not None:
            try:
                converted_items.append(convert_item(type_class, item))
            except Exception as e:
                if strict:
                    raise e
                else:
                    continue
    return converted_items


def area_filter(items, area, strict=False):
    """过滤转换出现在指定列表内的元素列表

    :param items: 元素列表
    :param area: 指定列表
    :param strict: 严格模式（转换失败抛出异常）
    :return: 过滤结果
    """
    if len(area) == 0:
        return []

    type_class = type(area[0])
    converted_items = type_filter(items, type_class, strict)
    return list(set(area) & set(converted_items))


def list_filter(items, param, strict=False):
    """自动过滤转换元素列表

    :param items: 元素列表
    :param param: 过滤参数 类型/指定列表
    :param strict: 严格模式（转换失败抛出异常）
    :return: 过滤结果
    """
    if isinstance(param, set):
        param = list(param)

    if isinstance(param, (tuple, list)):
        return area_filter(items, param, strict)
    else:
        return type_filter(items, param, strict)


def value_filter(value, param, strict=False):
    """自动过滤转换元素

    :param value: 元素
    :param param: 过滤参数 类型/指定列表
    :param strict: 严格模式（转换失败抛出异常）
    :return: 过滤转换结果
    """
    ret = list_filter([value], param, strict)
    if ret:
        return ret[0]
    return None


def sort(data, key=None, seq=None, reverse=False):
    """排序

    :param data: 列表数据
    :param key: 获取基准值方法
    :param seq: 基准队列
    :param reverse: 是否反序
    :return: 列表本身
    """
    key = key or (lambda x: x)
    if seq:
        sort_key = lambda x: find(seq, key(x))
    else:
        sort_key = key

    return data.sort(key=sort_key, reverse=reverse)


def find(seq, val):
    if not seq:
        return -1

    try:
        return seq.index(val)
    except:
        return -1
