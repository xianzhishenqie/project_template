from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView

from sv_auth.models import User, Owner
from sv_auth.utils.org import can_operate_user
from sv_auth.utils.owner import can_operate_obj


class IsSuperAdmin(BasePermission):
    """
    超级管理员
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsAdmin(BasePermission):
    """
    普通管理员
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsAdminOrReadOnly(BasePermission):
    """
    普通管理员只读
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            (request.method in SAFE_METHODS or request.user.is_admin)
        )


def check_superuser_permission(user: User) -> None:
    """检查是否超级管理员

    :param user: 用户
    """
    if not user.is_superuser:
        raise PermissionDenied()


def check_adminuser_permission(user: User) -> None:
    """检查是否普通管理员

    :param user: 用户
    """
    if user.group == User.Group.STAFF:
        raise PermissionDenied()


def check_org_permission(user: User, target_user: User) -> None:
    """检查是操作用户能否修改目标用户

    :param user: 操作用户
    :param target_user: 目标用户
    """
    if not can_operate_user(user, target_user):
        raise PermissionDenied()


def check_operate_permission(user: User, obj: Owner) -> None:
    """检查是操作用户能否修改目标数据

    :param user: 操作用户
    :param obj: 目标数据
    """
    if not can_operate_obj(user, obj):
        raise PermissionDenied()
