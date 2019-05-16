from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sv_base.extensions.db.models import IntChoice
from sv_base.extensions.db.manager import MManager
from sv_base.extensions.resource.models import ResourceModel


class MUserManager(MManager, UserManager):
    pass


class Organization(models.Model):
    """
    组织
    """
    name = models.CharField(_('x_auth_name'), max_length=100, blank=True, default='')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, default=None)

    class Meta:
        verbose_name = _('x_auth_organization')
        verbose_name_plural = _('x_auth_organizations')


class User(ResourceModel, AbstractUser):
    """
    用户
    """
    logo = models.ImageField(_('x_auth_logo'), upload_to='user_logo', blank=True, default='')
    nickname = models.CharField(_('x_auth_nickname'), max_length=100, blank=True, default='')
    name = models.CharField(_('x_auth_fullname'), max_length=100, blank=True, default='')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, default=None)

    class Group(IntChoice):
        ADMIN = 1
        NORMAL = 2

    class Status(IntChoice):
        DELETE = 0
        NORMAL = 1
    status = models.PositiveIntegerField(_('x_auth_status'), choices=Status.choices(), default=Status.NORMAL)

    objects = MUserManager({'status': Status.DELETE})
    original_objects = models.Manager()

    @property
    def rep_name(self):
        return self.nickname or self.username

    @property
    def group(self):
        if self.is_superuser:
            return None

        group = self.groups.first()
        if not group:
            return None

        return group.pk

    @property
    def is_admin(self):
        if self.is_superuser:
            return True

        return self.group == User.Group.ADMIN


class Creator(models.Model):
    """
    用户创建的资源
    """
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    create_time = models.DateTimeField(_('x_auth_create_time'), default=timezone.now)

    class Meta:
        abstract = True


class Modifier(Creator):
    """
    用户可修改的资源
    """
    modify_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    modify_time = models.DateTimeField(_('x_auth_modify_time'), default=timezone.now)

    class Meta:
        abstract = True


class Owner(Modifier):
    """
    用户拥有的资源
    """
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')

    class PublicMode(IntChoice):
        PRIVATE = 0
        INNER = 1
        OUTER = 2
    public_mode = models.PositiveIntegerField(_('x_auth_public_mode'), choices=PublicMode.choices(), default=PublicMode.PRIVATE)
    public_operate = models.BooleanField(_('x_auth_public_operate'), default=False)

    class Meta:
        abstract = True
