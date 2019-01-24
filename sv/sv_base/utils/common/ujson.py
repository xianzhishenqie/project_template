from django.utils import six


def get_index_data(data):
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
    return _parse_index_data(data['d'], data['i'])


def _convert_index_data(data, index_pool):
    if isinstance(data, (six.string_types, six.integer_types)):
        if data in index_pool['index']:
            index = index_pool['index'][data]
        else:
            index = index_pool['counter']
            index_pool['index'][data] = index
            index_pool['counter'] += 1
        return index
    elif isinstance(data, list):
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
    if isinstance(data, six.integer_types):
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
