from sv_base.patch.django import monkey_patch as django_monkey_patch
from sv_base.patch.rest import monkey_patch as rest_monkey_patch


def sync_init():
    django_monkey_patch()
    rest_monkey_patch()
