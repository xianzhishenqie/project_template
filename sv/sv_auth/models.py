from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django_enumfield import enum

from sv_base.utils.db.manager import MManager
from sv_base.utils.resource.models import ResourceModel


class MUserManager(MManager, UserManager):
    pass


class Organization(models.Model):
    """
    组织
    """
    name = models.CharField(max_length=100, default='')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, default=None)


class User(ResourceModel, AbstractUser):
    """
    用户
    """
    logo = models.ImageField(upload_to='user_logo', default='')
    nickname = models.CharField(max_length=100, default='')
    name = models.CharField(max_length=100, default='')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, default=None)

    class Group(enum.Enum):
        ADMIN = 1
        NORMAL = 2
    class Status(enum.Enum):
        DELETE = 0
        NORMAL = 1
    status = enum.EnumField(Status, default=Status.NORMAL)
    extra = models.TextField(default='')

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


class Owner(models.Model):
    """
    用户拥有的资源
    """
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')

    class PublicMode(enum.Enum):
        PRIVATE = 0
        INNER = 1
        OUTER = 2
    public_mode = enum.EnumField(PublicMode, default=PublicMode.PRIVATE)
    public_operate = models.BooleanField(default=False)

    create_time = models.DateTimeField(default=timezone.now)
    modify_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    modify_time = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
