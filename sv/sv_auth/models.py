# -*- coding: utf-8 -*-
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

from sv_base.utils.common.uenum import Enum
from sv_base.utils.models.manager import MManager
from sv_base.utils.resource.models import ResourceModel


class MUserManager(MManager, UserManager):
    pass


# 1级省厅  2级地市
class Organization(models.Model):
    name = models.CharField(max_length=100, default='')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, default=None)


class User(ResourceModel, AbstractUser):
    logo = models.ImageField(upload_to='user_logo', default='')
    nickname = models.CharField(max_length=100, default='')
    name = models.CharField(max_length=100, default='')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, default=None)

    Group = Enum(
        ADMIN=1,
        NORMAL=2,
    )
    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)
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
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')

    PublicMode = Enum(
        PRIVATE=0,
        INNER=1,
        OUTER=2,
    )
    public_mode = models.PositiveIntegerField(default=PublicMode.PRIVATE)
    public_operate = models.BooleanField(default=False)

    create_time = models.DateTimeField(default=timezone.now)
    modify_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    modify_time = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
