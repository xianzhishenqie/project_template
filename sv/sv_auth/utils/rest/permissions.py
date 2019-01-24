from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS

from sv_auth.models import User
from sv_auth.utils.org import can_operate_user
from sv_auth.utils.owner import can_operate_obj



class IsSuperAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.method in SAFE_METHODS or request.user.is_admin)
        )


def check_superuser_permission(user):
    if not user.is_superuser:
        raise PermissionDenied()


def check_adminuser_permission(user):
    if user.group == User.Group.STAFF:
        raise PermissionDenied()


def check_org_permission(user, target_user):
    if not can_operate_user(user, target_user):
        raise PermissionDenied()


def check_operate_permission(user, obj):
    if not can_operate_obj(user, obj):
        raise PermissionDenied()
