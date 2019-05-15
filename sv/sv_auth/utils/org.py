import logging

from django.db.models import Q

from sv_auth import app_settings
from sv_auth.models import User


logger = logging.getLogger(__name__)


def org_level(org):
    """获取组织级别。

    :param org: 组织对象
    :return: 组织级别
    """
    if not app_settings.ENABLE_ORG:
        return 0

    level = 1
    while org.parent:
        level += 1
        org = org.parent
    return level


def get_org_level(user):
    """获取用户组织级别。

    :param user: 用户
    :return: 组织级别
    """
    if not app_settings.ENABLE_ORG:
        return 0

    if user.is_superuser:
        return 0

    if not user.organization:
        _illegal_user(user)

    return org_level(user.organization)


def can_add_org(operate_user, parent):
    """判断用户是否能添加子组织。

    :param operate_user: 操作用户
    :param parent: 目标父组织
    :return: bool
    """
    if not app_settings.ENABLE_ORG:
        return False

    t_org_level = None
    if parent:
        # 操作目标组织等级
        t_org_level = org_level(parent)
        # 目标组织深度超过限制，不能添加
        if t_org_level >= app_settings.ORG_DEPTH:
            return False

    if operate_user.is_superuser:
        return True

    if not parent:
        return False

    # 普通用户不能添加
    if operate_user.group != User.Group.ADMIN:
        return False

    # 操作用户所属组织等级
    o_org_level = get_org_level(operate_user)
    o_org = operate_user.organization
    t_org = parent
    # 目标组织等级高于用户组织等级时, 用户不能填加组织
    if o_org_level > t_org_level:
        return False
    else:
        # 判断目标组织是否属于操作用户组织
        while t_org:
            if t_org == o_org:
                return True
            t_org = t_org.parent

        return False


def can_operate_org(operate_user, org):
    """判断用户是否能修改组织。

    :param operate_user: 操作用户
    :param org: 目标组织
    :return: bool
    """
    if not app_settings.ENABLE_ORG:
        return False

    if operate_user.is_superuser:
        return True

    # 普通用户不能修改
    if operate_user.group != User.Group.ADMIN:
        return False

    # 操作用户所属组织等级
    o_org_level = get_org_level(operate_user)
    # 操作目标组织等级
    t_org_level = org_level(org)
    o_org = operate_user.organization
    t_org = org
    # 目标组织等级高于等于用户组织等级时, 用户不能修改组织
    if o_org_level >= t_org_level:
        return False
    else:
        # 判断目标组织是否属于操作用户组织
        while t_org.parent:
            if t_org.parent == o_org:
                return True
            t_org = t_org.parent

        return False


def can_add_user(operate_user, group, org=None):
    """判断用户是否能添加用户。

    :param operate_user: 操作用户
    :param group: 目标组
    :param org: 目标组织
    :return: bool
    """
    if operate_user.is_superuser:
        return True

    if not group:
        return False

    # 普通用户不能添加用户
    if operate_user.group != User.Group.ADMIN:
        return False

    if app_settings.ENABLE_ORG:
        if not org:
            return False

        # 操作用户所属组织等级
        o_org_level = get_org_level(operate_user)
        # 操作目标组织等级
        t_org_level = org_level(org)
        o_org = operate_user.organization
        t_org = org

        if o_org_level == t_org_level:
            # 在同一组织下，只能创建普通用户
            return o_org == t_org and group > User.Group.ADMIN
        elif o_org_level < t_org_level:
            t_org = t_org.parent
            while t_org:
                # 操作属于自己组织的组织
                if t_org == o_org:
                    return True
                t_org = t_org.parent

            return False
        else:
            return False
    else:
        return group > User.Group.ADMIN


def can_operate_user(operate_user, target_user):
    """判断用户是否能修改用户。

    :param operate_user: 操作用户
    :param target_user: 目标用户
    :return: bool
    """
    if operate_user == target_user:
        return True
    if operate_user.is_superuser:
        return True
    if target_user.is_superuser:
        return False

    # 普通用户不能修改其他用户
    if operate_user.group != User.Group.ADMIN:
        return False

    if app_settings.ENABLE_ORG:
        # 操作用户所属组织等级
        o_org_level = get_org_level(operate_user)
        # 目标用户所属组织等级
        t_org_level = get_org_level(target_user)
        o_org = operate_user.organization
        t_org = target_user.organization

        if o_org_level == t_org_level:
            # 在同一组织下
            return o_org == t_org
        elif o_org_level < t_org_level:
            # 判断目标用户组织是否属于操作用户组织
            while t_org.parent:
                if t_org.parent == o_org:
                    return True
                t_org = t_org.parent

            return False
        else:
            return False
    else:
        return True


def _illegal_user(user):
    msg = 'illegal user[%s]!' % user.pk
    logger.error(msg)
    raise Exception(msg)


def get_filter_org_params(user, field=None):
    """获取基于组织的查询条件。

    :param user: 操作用户
    :param field: 组织关联字段
    :return: 查询条件
    """
    if not app_settings.ENABLE_ORG:
        return Q()

    user_org_level = get_org_level(user)
    if user_org_level == 0:
        return Q()

    if field:
        base_key = '{}__organization'.format(field)
    else:
        base_key = 'organization'

    params = Q(**{base_key: user.organization})
    for i in range(app_settings.ORG_DEPTH - user_org_level):
        base_key = '{}{}'.format(base_key, '__parent')
        params = params | Q(**{base_key: user.organization})

    return params


def filter_org_queryset(user, queryset, field=None):
    """添加基于组织的过滤查询。

    :param user: 操作用户
    :param queryset: 查询queryset
    :param field: 组织关联字段
    :return: 查询queryset
    """
    if not app_settings.ENABLE_ORG:
        return queryset

    return queryset.filter(get_filter_org_params(user, field))
