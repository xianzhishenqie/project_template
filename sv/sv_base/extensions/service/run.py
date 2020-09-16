from django.conf import settings

from sv_base.extensions.service.base import EventSender, get_config


def run(services=None, name=None, backdoor_port=None):
    from nameko.cli.run import import_service, run as nameko_run

    if services is None:
        services = [EventSender]
        for module_name in settings.SERVICE_MODULES:
            services.extend(import_service(module_name))

    if services:
        config = get_config(settings.NAMEKO_CONFIG, name=name)
        nameko_run(services, config, backdoor_port=backdoor_port)
