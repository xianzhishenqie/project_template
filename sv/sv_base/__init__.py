from sv_base.extensions.project.app import load_app_settings

from sv_base.patch.python import monkey_patch as python_monkey_patch
from sv_base.patch.django import monkey_patch as django_monkey_patch
from sv_base.patch.rest import monkey_patch as rest_monkey_patch


app_settings = load_app_settings(__package__)


def sync_init():
    python_monkey_patch()
    django_monkey_patch()
    rest_monkey_patch()
