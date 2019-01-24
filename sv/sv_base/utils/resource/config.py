# -*- coding: utf-8 -*-
from django.utils import six

from .meta import ResourceOption


resource_classes = set()


class ResourceBase(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(ResourceBase, cls).__new__(cls, name, bases, attrs)
        # 解析资源配置选项
        if new_class.model:
            new_class.model._resource_meta = ResourceOption(new_class.model, new_class)

        resource_classes.add(new_class)
        return new_class


# 资源配置父类
class Resource(six.with_metaclass(ResourceBase)):
    model = None
    options = None
