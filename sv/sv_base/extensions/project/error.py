import enum

from rest_framework.exceptions import ErrorDetail

from .trans import Trans as _


default_errors = dict(
    ERROR=_('x_error'),
    NO_PERMISSION=_('x_no_permission'),
    INVALID_PARAMS=_('x_invalid_params'),
    INVALID_VALUE=_('x_invalid_value'),
    DUPLICATE_SUBMIT=_('x_duplicate_submit'),
    DUPLICATE_REQUEST=_('x_duplicate_request'),
    SAVE_FAILED=_('x_save_failed'),
)


def generate_error_code(attr_name):
    """生成错误码。

    :param attr_name: 属性名称
    :return: 错误码
    """
    return attr_name


for key, value in default_errors.items():
    value.code = generate_error_code(key)


class ErrorMeta(enum.EnumMeta):
    def __new__(mcs, cls, bases, classdict):
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
