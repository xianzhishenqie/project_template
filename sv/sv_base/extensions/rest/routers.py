import re

from rest_framework.routers import DefaultRouter


def get_default_router(viewsets):
    """获取默认viewsets路由

    :param viewsets: viewsets
    :return: viewsets路由
    """
    router = DefaultRouter()
    for viewset in viewsets:
        names = re.findall(r'[A-Z][a-z]+', viewset.__name__)
        names = [s.lower() for s in names[:-2]]
        name = '_'.join(names) + 's'
        base_name = '-'.join(names)
        router.register(name, viewset, base_name=base_name)
    return router


def rest_path(viewsets):
    """获取viewsets路由url

    :param viewsets: viewsets
    :return: viewsets路由
    """
    router = get_default_router(viewsets)
    return router.urls
