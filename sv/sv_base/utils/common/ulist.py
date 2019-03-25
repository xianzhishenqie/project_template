from typing import Union


def convert_item(type_class: type, item: object) -> object:
    """对元素进行类型强制转换

    :param type_class: 类型
    :param item: 元素
    :return: 转换值
    """
    return type_class(item)


def type_filter(items: list, type_class: type, strict: bool = False) -> list:
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


def area_filter(items: list, area: Union[tuple, list], strict: bool = False) -> list:
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


def list_filter(items: list, param: Union[type, set, tuple, list], strict: bool = False) -> list:
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


def value_filter(value: object, param: Union[type, set, tuple, list], strict: bool = False) -> object:
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
