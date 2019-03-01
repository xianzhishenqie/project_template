import copy
import enum

from django.utils import six
from rest_framework.exceptions import ErrorDetail

from sv_base.utils.common.utext import Txt, trans as _


class CommonError(enum.Enum):
    ERROR = _('服务器繁忙')

    NO_PERMISSION = _('无操作权限')

    INVALID_PARAMS = _('无效的参数')

    INVALID_VALUE = _('参数值无效')

    DUPLICATE_SUBMIT = _('重复的提交')

    DUPLICATE_REQUEST = _('重读的请求')

    SAVE_FAILED = _('数据保存失败')


class Error:
    """
    定义错误类 错误码->错误描述
    """
    error = Enum()

    def __new__(cls, **errors) -> Enum:
        """初始化错误字典

        :param errors: 定义错误的字典
        :return: 错误枚举
        """
        custom_errors = copy.copy(common_error.source)
        for attr_name, error_desc in errors.items():
            error_code = cls.generate_error_code(attr_name)
            if isinstance(error_desc, Txt):
                error_desc.code = error_code
                detail = error_desc
            elif isinstance(error_desc, six.string_types):
                detail = ErrorDetail(error_desc, error_code)
            else:
                error_desc.code = error_code
                detail = error_desc
            custom_errors[attr_name] = detail
        cls.error.update(**custom_errors)
        return Enum(**custom_errors)

    @classmethod
    def generate_error_code(cls, attr_name: str) -> str:
        """生成错误码。

        :param attr_name: 属性名称
        :return: 错误码
        """
        return attr_name


error = Error.error
