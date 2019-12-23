import re

from django.conf.urls import url


def get_default_router(websocket_classes):
    """获取默认的websocket路由

    :param websocket_classes: websocket类
    :return: websocket路由
    """
    routers = []
    for websocket_class in websocket_classes:
        name = get_websocket_router_name(websocket_class)
        router = url(r'{}/'.format(name), websocket_class)
        routers.append(router)
    return routers


def ws_path(websocket_classes):
    """获取websocket路由

    :param websocket_classes: websocket类
    :return: websocket路由
    """
    routers = get_default_router(websocket_classes)
    return routers


def get_websocket_router_name(websocket):
    """
    获取websocket路由名称信息
    :param websocket: websocket
    :return: 路由名称信息
    """
    if hasattr(websocket, 'router_name'):
        if callable(websocket.router_name):
            name = websocket.router_name()
        else:
            name = websocket.router_name
    else:
        names = re.findall(r'[A-Z][a-z]+', websocket.__name__)
        names = [s.lower() for s in names[:-1]]
        name = '_'.join(names)

    return name
