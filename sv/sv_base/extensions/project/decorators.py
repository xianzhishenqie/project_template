from rest_framework import exceptions
from sv_base.utils.base.func import sync_func
from sv_base.utils.base.text import md5
from .error import Error


def _get_serializer_key(serializer, fields=None):
    """
    获取序列化键

    :param serializer: 序列化对象
    :param fields: 关联字段
    :return: 序列化键
    """
    validated_data = serializer.validated_data
    fields = fields if fields is not None else validated_data.keys()
    values = [str(validated_data.get(field) or '') for field in fields]
    value_str = '|'.join(values)
    serializer_class = serializer.__class__
    return md5(f'{serializer_class.__module__}.{serializer_class.__qualname__}:{value_str}')


def _exit_perform_create(*args, **kwargs):
    """
    退出创建
    """
    raise exceptions.ParseError(Error.DUPLICATE_SUBMIT)


def sync_perform_create(fields=None):
    """
    同步viewsets创建方法
    """

    def key_func(func, view, serializer, *args, **kwargs):
        serializer_key = _get_serializer_key(serializer, fields)
        return f'perform_create_key:{serializer_key}'

    return sync_func(key_func, timeout=3, exit_func=_exit_perform_create)
