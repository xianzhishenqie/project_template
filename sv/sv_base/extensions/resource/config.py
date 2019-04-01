from __future__ import annotations

from typing import Optional, Type

from django.db.models import Model
from django.utils import six

from .meta import DataOption


resource_classes = set()


class ResourceBase(type):
    """
    资源配置元类，添加配置选项
    """
    def __new__(mcs, name: str, bases: tuple, attrs: dict) -> ResourceBase:
        new_class = super(ResourceBase, mcs).__new__(mcs, name, bases, attrs)
        # 解析资源配置选项
        model = getattr(new_class, 'model', None)
        if model:
            model._resource_meta = ResourceOption(model, new_class)

        resource_classes.add(new_class)
        return new_class


class Resource(six.with_metaclass(ResourceBase)):
    """
    资源配置父类
    """
    model = None
    options = None


class ResourceOption:
    """
    资源处理配置
    """
    def __init__(self, cls: Type[Model], resource: Optional[ResourceBase] = None) -> None:
        # 初始化所有拥有资源, 只有根资源有
        self.root_own = []
        # 初始化资源配置
        self.options = {}
        name_fields_map = {field.name: field for field in cls._meta.fields}
        attname_fields_map = {field.attname: field for field in cls._meta.fields}
        self.valid_fields_map = dict(name_fields_map, **attname_fields_map)
        self.fields_map = name_fields_map

        # 解析资源选项
        options = getattr(resource, 'options', ())
        if not options:
            options = ({},)
        for option in options:
            data_option = DataOption(cls, **option)
            self.set_option(data_option)

    @classmethod
    def generate_root_model_key(cls, root_model: Optional[Type[Model]] = None) -> str:
        """根资源表唯一key

        :param root_model: 根资源模型类
        :return: 唯一key
        """
        return root_model._meta.db_table if root_model else '_default'

    @classmethod
    def generate_root_parent_model_key(cls, root_model: Type[Model], parent_model: Type[Model]) -> str:
        """父资源表唯一key

        :param root_model: 根资源模型类
        :param parent_model: 父资源模型类
        :return: 唯一key
        """
        return '%s:%s' % (root_model._meta.db_table, parent_model._meta.db_table)

    def set_option(self, data_option: DataOption) -> None:
        """设置数据处理配置

        :param data_option: 数据处理配置
        """
        root_model_key = self.generate_root_model_key(data_option.root_model)
        self.options[root_model_key] = data_option

    def get_option(self, root_model: Optional[Model] = None) -> DataOption:
        """获取数据处理配置

        :param root_model: 根资源表模型
        :return: 数据处理配置
        """
        root_model_key = self.generate_root_model_key(root_model)
        option = self.options.get(root_model_key, None)
        # 如果根据根资源表找不到对应的拥有资源，寻找默认的拥有资源
        if root_model and not option:
            option = self.options.get(self.generate_root_model_key(), None)
        return option
