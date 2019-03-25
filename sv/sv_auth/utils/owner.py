from django.db.models import Q, F, QuerySet

from sv_auth import app_settings
from sv_auth.models import User, Owner


def get_filter_owner_params(user: User) -> Q:
    """获取基于用户的数据查询条件。

    :param user: 查询用户
    :return: 查询条件
    """
    if user.is_superuser:
        return Q(pk=F('pk'))

    if user.is_admin:
        # 管理员 能查看'同级'/'下级'/'完全公开'的
        params = Q(public_mode=Owner.PublicMode.OUTER) | Q(user__organization=user.organization)
        org_key = 'user__organization'
        for i in range(1, app_settings.ORG_DEPTH):
            org_key = '{}{}'.format(org_key, '__parent')
            params = params | Q(**{org_key: user.organization})

        return params
    else:
        # 普通用户 能查看'自己'/'同级内部公开'/'完全公开'的
        return Q(user=user) | \
               Q(user__organization=user.organization, public_mode=Owner.PublicMode.INNER) | \
               Q(public_mode=Owner.PublicMode.OUTER)


def filter_owner_queryset(user: User, queryset: QuerySet) -> QuerySet:
    """添加基于用户的过滤查询。

    :param user: 操作用户
    :param queryset: 查询queryset
    :return: 查询queryset
    """
    return queryset.filter(get_filter_owner_params(user))


def get_filter_operate_params(user: User) -> Q:
    """获取基于用户的数据操作查询条件。

    :param user: 操作用户
    :return: 查询条件
    """
    if user.is_superuser:
        return Q()

    if user.is_admin:
        # 管理员 能操作'同级'/'下级'/'完全公开并公开操作'
        params = Q(public_mode=Owner.PublicMode.OUTER, public_operate=True) | Q(user__organization=user.organization)
        org_key = 'user__organization'
        for i in range(1, app_settings.ORG_DEPTH):
            org_key = '{}{}'.format(org_key, '__parent')
            params = params | Q(**{org_key: user.organization})

        return params
    else:
        # 普通用户 能查看'自己'/'同级内部公开并公开操作'/'完全公开并公开操作'的
        return Q(user=user) | \
               Q(user__organization=user.organization, public_mode=Owner.PublicMode.INNER, public_operate=True) | \
               Q(public_mode=Owner.PublicMode.OUTER, public_operate=True)


def filter_operate_queryset(user: User, queryset: QuerySet) -> QuerySet:
    """添加基于用户的操作过滤查询。

    :param user: 操作用户
    :param queryset: 查询queryset
    :return: 查询queryset
    """
    return queryset.filter(get_filter_operate_params(user))


def can_operate_obj(user: User, obj: Owner) -> bool:
    """判断用户能否操作对象

    :param user: 操作用户
    :param obj: 操作对象
    :return: bool
    """
    if user.is_superuser:
        return True

    # 公开数据并公开操作权限
    if obj.public_mode == Owner.PublicMode.OUTER and obj.public_operate:
        return True

    if not user.organization:
        return False

    if not obj.user.organization:
        return False

    if user.is_admin:
        # 管理员可操作同级或下级组织用户的资源数据
        check = user.organization == obj.user.organization

        parent = obj.user.organization
        for i in range(1, app_settings.ORG_DEPTH):
            parent = getattr(parent, 'parent', None)
            if parent:
                check = check or user.organization == parent
            else:
                break

        if check:
            return True
        else:
            return False
    else:
        # 普通用户可操作自己和同级用户公开操作的资源
        if user == obj.user:
            return True
        elif (user.organization == obj.user.organization
              and obj.public_mode == Owner.PublicMode.INNER
              and obj.public_operate):
            return True
        else:
            return False
