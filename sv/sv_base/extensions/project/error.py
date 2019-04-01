from __future__ import annotations

import enum

from rest_framework.exceptions import ErrorDetail

from .trans import Trans as _


default_errors = dict(
    ERROR=_('服务器繁忙'),
    NO_PERMISSION=_('无操作权限'),
    INVALID_PARAMS=_('无效的参数'),
    INVALID_VALUE=_('参数值无效'),
    DUPLICATE_SUBMIT=_('重复的提交'),
    DUPLICATE_REQUEST=_('重复的请求'),
    SAVE_FAILED=_('数据保存失败'),
)


def generate_error_code(attr_name: str) -> str:
    """生成错误码。

    :param attr_name: 属性名称
    :return: 错误码
    """
    return attr_name


for key, value in default_errors.items():
    value.code = generate_error_code(key)


class ErrorMeta(enum.EnumMeta):
    def __new__(mcs, cls: str, bases: tuple, classdict: enum._EnumDict) -> ErrorMeta:
        """初始化格式错误字典

        :param cls: 当前类名
        :param bases: 父类
        :param classdict: 类属性
        :return: 当前类
        """
        errors = []
        for attr_name, error_desc in list(classdict.items()):
            if attr_name.isupper():
                error_code = generate_error_code(attr_name)
                if isinstance(error_desc, _):
                    error_desc.code = error_code
                    detail = error_desc
                elif isinstance(error_desc, str):
                    detail = ErrorDetail(error_desc, error_code)
                else:
                    error_desc.code = error_code
                    detail = error_desc

                errors.append((attr_name, detail))
                classdict._member_names.remove(attr_name)
                classdict._last_values.remove(error_desc)
                classdict.pop(attr_name)

        for attr_name, detail in list(default_errors.items()) + errors:
            classdict[attr_name] = detail

        return enum.EnumMeta.__new__(mcs, cls, bases, classdict)
