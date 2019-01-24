# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.base import ModelBase

from sv_base.utils.common.utext import rk


resource_classes = set()


# model 资源表元类
class ResourceBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(ResourceBase, cls).__new__

        parents = [b for b in bases if isinstance(b, ResourceBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        new_class = super_new(cls, name, bases, attrs)
        if new_class._meta.abstract:
            return new_class

        resource_classes.add(new_class)
        return new_class


class ResourceModel(models.Model):
    __metaclass__ = ResourceBase

    resource_id = models.CharField(max_length=64, default=rk)

    class Meta:
        abstract = True

