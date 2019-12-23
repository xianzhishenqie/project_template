import re

from django.conf import settings

from rest_framework.routers import DefaultRouter


def get_default_router(viewsets):
    """获取默认viewsets路由

    :param viewsets: viewsets
    :return: viewsets路由
    """
    router = DefaultRouter()
    if not settings.DEBUG:
        router.include_root_view = False

    for viewset in viewsets:
        name, base_name = get_viewset_router_name(viewset)
        router.register(name, viewset, base_name=base_name)
    return router


def rest_path(viewsets):
    """获取viewsets路由url

    :param viewsets: viewsets
    :return: viewsets路由
    """
    router = get_default_router(viewsets)
    return router.urls


def get_viewset_router_name(viewset):
    """
    获取viewset路由名称信息
    :param viewset: viewset
    :return: 路由名称信息
    """
    if hasattr(viewset, 'router_name'):
        if callable(viewset.router_name):
            return viewset.router_name()
        else:
            return viewset.router_name
    else:
        names = re.findall(r'[A-Z][a-z]+', viewset.__name__)
        names = [s.lower() for s in names[:-2]]
        name = '_'.join(names) + 's'
        base_name = '-'.join(names)

    return name, base_name
