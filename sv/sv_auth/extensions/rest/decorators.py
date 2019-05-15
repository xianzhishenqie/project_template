import functools

from sv_auth.utils.org import filter_org_queryset
from sv_auth.utils.owner import filter_owner_queryset


def org_queryset(func):
    """根据组织架构权限过滤资源查询

    :param func: get_queryset方法
    :return: 过滤资源结果集
    """
    @functools.wraps(func)
    def wrapper(view, *args, **kwargs):
        queryset = func(view, *args, **kwargs)
        return filter_org_queryset(view.request.user, queryset)

    return wrapper


def owner_queryset(func):
    """根据资源拥有者过滤资源查询权限

    :param func: get_queryset方法
    :return: 过滤资源结果集
    """
    @functools.wraps(func)
    def wrapper(view, *args, **kwargs):
        queryset = func(view, *args, **kwargs)
        return filter_owner_queryset(view.request.user, queryset)

    return wrapper
