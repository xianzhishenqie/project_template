
import re

from django.conf.urls import url


def get_default_router(websocket_classes: list) -> list:
    """获取默认的websocket路由

    :param websocket_classes: websocket类
    :return: websocket路由
    """
    routers = []
    for websocket_class in websocket_classes:
        names = re.findall(r'[A-Z][a-z]+', websocket_class.__name__)
        names = [s.lower() for s in names[:-1]]
        name = '_'.join(names)
        router = url(r'{}/'.format(name), websocket_class)
        routers.append(router)
    return routers


def ws_path(websocket_classes: list) -> list:
    """获取websocket路由

    :param websocket_classes: websocket类
    :return: websocket路由
    """
    routers = get_default_router(websocket_classes)
    return routers
