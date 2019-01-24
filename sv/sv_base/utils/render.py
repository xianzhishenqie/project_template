import copy
from django.shortcuts import render

from sv_base.utils.app import get_app_service_name


class AppRender:

    def __init__(self, module, template_path=None):
        self.path_parts = get_app_service_name(module)
        if template_path:
            self.path_parts.append(template_path)

    def render(self, request, template_name, context=None, content_type=None, status=None, using=None):
        path_parts = copy.copy(self.path_parts)
        path_parts.append(template_name)
        template_name = '/'.join(path_parts)

        return render(request, template_name, context, content_type, status, using)


def get_app_render(module, template_path=None):
    return AppRender(module, template_path).render
