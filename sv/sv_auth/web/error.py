from enum import Enum
from sv_base.utils.error import ErrorMeta
from sv_base.utils.common.utext import Trans as _


class Error(Enum, metaclass=ErrorMeta):
    AUTHENTICATION_FAILED = _('用户名或密码错误')
