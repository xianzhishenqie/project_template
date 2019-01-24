import logging

from django.db.models import Q

from sv_auth import app_settings
from sv_auth.models import User


logger = logging.getLogger(__name__)



def org_level(org):
    level = 1
    while org.parent:
        level += 1
        org = org.parent
    return level


def get_org_level(user):
    if user.is_superuser:
        return 0

    if not user.organization:
        _illegal_user(user)

    return org_level(user.organization)


def can_add_org(operate_user, parent):
    if parent:
        l = org_level(parent)
        if l >= app_settings.ORG_DEPTH:
            return False

    if operate_user.is_superuser:
        return True

    if not parent:
        return False

    if operate_user.group != User.Group.ADMIN:
        return False

    o_org_level = get_org_level(operate_user)
    t_org_level = org_level(parent)
    o_org = operate_user.organization
    t_org = parent
    if o_org_level > t_org_level:
        return False
    else:
        while t_org:
            if t_org == o_org:
                return True
            t_org = t_org.parent

        return False


def can_operate_org(operate_user, org):
    if operate_user.is_superuser:
        return True

    if operate_user.group != User.Group.ADMIN:
        return False

    o_org_level = get_org_level(operate_user)
    t_org_level = org_level(org)
    o_org = operate_user.organization
    t_org = org
    if o_org_level >= t_org_level:
        return False
    else:
        while t_org.parent:
            if t_org.parent == o_org:
                return True
            t_org = t_org.parent

        return False


def can_add_user(operate_user, org, group):
    if operate_user.is_superuser:
        return True

    if not org or not group:
        return False

    if operate_user.group != User.Group.ADMIN:
        return False

    o_org_level = get_org_level(operate_user)
    t_org_level = org_level(org)
    o_org = operate_user.organization
    t_org = org

    if o_org_level == t_org_level:
        return o_org == t_org and group > User.Group.ADMIN
    elif o_org_level < t_org_level:
        t_org = t_org.parent
        while t_org:
            if t_org == o_org:
                return True
            t_org = t_org.parent

        return False
    else:
        return False


def can_operate_user(operate_user, target_user):
    if operate_user == target_user:
        return True
    if operate_user.is_superuser:
        return True
    if target_user.is_superuser:
        return False

    if operate_user.group != User.Group.ADMIN:
        return False

    o_org_level = get_org_level(operate_user)
    t_org_level = get_org_level(target_user)
    o_org = operate_user.organization
    t_org = target_user.organization

    if o_org_level == t_org_level:
        return o_org == t_org
    elif o_org_level < t_org_level:
        while t_org.parent:
            if t_org.parent == o_org:
                return True
            t_org = t_org.parent

        return False
    else:
        return False


def _illegal_user(user):
    msg = 'illegal user[%s]!' % user.pk
    logger.error(msg)
    raise Exception(msg)


def get_filter_org_params(user, field=None):
    l = get_org_level(user)
    if l == 0:
        return Q()

    if field:
        base_key = '{}__organization'.format(field)
    else:
        base_key = 'organization'

    params = Q(**{base_key: user.organization})
    for i in range(app_settings.ORG_DEPTH - l):
        base_key = '{}{}'.format(base_key, '__parent')
        params = params | Q(**{base_key: user.organization})

    return params


def filter_org_queryset(user, queryset, field=None):
    return queryset.filter(get_filter_org_params(user, field))
