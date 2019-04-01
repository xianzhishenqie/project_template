from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from sv_base.extensions.project.app import get_sv_routers


config = {}
websocket_routers = get_sv_routers()
if websocket_routers:
    config['websocket'] = AuthMiddlewareStack(
        URLRouter([url(r'^ws/', URLRouter(get_sv_routers()))])
    )

application = ProtocolTypeRouter(config)
