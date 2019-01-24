
import re

from django.conf.urls import url


def get_default_router(websocket_classes):
    routers = []
    for websocket_class in websocket_classes:
        names = re.findall(r'[A-Z][a-z]+', websocket_class.__name__)
        names = [s.lower() for s in names[:-1]]
        name = '_'.join(names)
        router = url(r'{}/'.format(name), websocket_class)
        routers.append(router)
    return routers


def ws_path(websocket_classes):
    routers = get_default_router(websocket_classes)
    return routers
