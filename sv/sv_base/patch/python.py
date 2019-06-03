"""
python补丁

"""
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


def monkey_patch():
    """打补丁

    """
    json.JSONEncoder.default = jsonencoder_default
