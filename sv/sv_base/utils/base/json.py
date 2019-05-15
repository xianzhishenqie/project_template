
def get_index_data(data):
    """获取json索引数据

    :param data: json数据
    :return: json索引和数据
    """
    index_pool = {
        'index': {},
        'counter': 1,
    }
    result = _convert_index_data(data, index_pool)
    index_data = {}
    for value, index in index_pool['index'].items():
        index_data[index] = value
    return {
        'i': index_data,
        'd': result
    }


def parse_index_data(data):
    """解析json索引数据

    :param data: json索引和数据
    :return: json数据
    """
    parsed_data = _parse_index_data(data['d'], data['i'])
    if not isinstance(parsed_data, dict):
        raise Exception('invalid index data')

    return parsed_data


def _convert_index_data(data, index_pool):
    """转换数据为索引（只会转换最终值为数字和字符串的值）。

    :param data: 数据值
    :param index_pool: 索引池
    :return: 索引数据
    """
    if isinstance(data, (str, int)):
        # 字符串/数字的值进行索引
        if data in index_pool['index']:
            # 如果索引已存在值，直接返回索引值
            index = index_pool['index'][data]
        else:
            # 如果索引不存在，添加索引
            index = index_pool['counter']
            index_pool['index'][data] = index
            index_pool['counter'] += 1
        return index
    elif isinstance(data, (tuple, list)):
        res = []
        for item in data:
            res.append(_convert_index_data(item, index_pool))
        return res
    elif isinstance(data, dict):
        res = {}
        for key, value in data.items():
            res[_convert_index_data(key, index_pool)] = _convert_index_data(value, index_pool)
        return res
    else:
        return data


def _parse_index_data(data, index_pool):
    """转换索引为数据。

    :param data: 索引
    :param index_pool: 索引池
    :return: 数据
    """
    if isinstance(data, int):
        return index_pool.get(data)
    elif isinstance(data, list):
        res = []
        for item in data:
            res.append(_parse_index_data(item, index_pool))
        return res
    elif isinstance(data, dict):
        res = {}
        for key, value in data.items():
            res[_parse_index_data(key, index_pool)] = _parse_index_data(value, index_pool)
        return res
    else:
        return data
