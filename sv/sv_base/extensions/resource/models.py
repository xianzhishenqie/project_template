from django.db import models
from django.db.models.base import ModelBase

from sv_base.utils.base.text import rk


resource_classes = set()


class ResourceBase(ModelBase):
    """
    model 资源表元类
    """
    def __new__(mcs, name, bases, attrs):
        super_new = super(ResourceBase, mcs).__new__

        parents = [b for b in bases if isinstance(b, ResourceBase)]
        if not parents:
            return super_new(mcs, name, bases, attrs)

        new_class = super_new(mcs, name, bases, attrs)
        if new_class._meta.abstract:
            return new_class

        resource_classes.add(new_class)
        return new_class


class ResourceModel(models.Model):
    """
    model 资源表类, 默认添加resource_id唯一字段
    """

    __metaclass__ = ResourceBase

    resource_id = models.CharField(max_length=64, default=rk, unique=True)

    class Meta:
        abstract = True


class PrimaryResourceModel(models.Model):
    """
    model 资源表类, 默认添加resource_id主键字段, 影响部分效率
    """

    __metaclass__ = ResourceBase

    resource_id = models.CharField(max_length=64, default=rk, primary_key=True)

    class Meta:
        abstract = True
