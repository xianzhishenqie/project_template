from enum import Enum
from sv_base.extensions.project.error import ErrorMeta
from sv_base.extensions.project.trans import Trans as _


class Error(Enum, metaclass=ErrorMeta):
    AUTHENTICATION_FAILED = _('用户名或密码错误')
