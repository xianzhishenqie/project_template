"""
python补丁

"""
import enum
import json


_jsonencoder_default = json.JSONEncoder.default


def jsonencoder_default(self, o):
    """json 默认序列化

    :param self: 编码器
    :param o: 序列化对象
    :return: 序列化结果
    """
    if hasattr(o, '__json__'):
        return o.__json__()
    else:
        return _jsonencoder_default(self, o)


@classmethod
def enum_values(cls, return_value=True):
    values = cls.__members__.values()
    if return_value:
        return [value.value for value in values]
    else:
        return list(values)


def monkey_patch():
    """打补丁

    """
    json.JSONEncoder.default = jsonencoder_default
    enum.Enum.values = enum_values
