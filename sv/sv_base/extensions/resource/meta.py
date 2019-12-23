from enum import IntEnum, Enum

from django.db import models
from django.db.models import Model, QuerySet
from django.utils.module_loading import import_string

from .exception import ResourceException


# 资源id名称
resource_key_name = 'resource_id'


# 无法序列化需要转换为字符串的字段类型
convert_string_fields = (
    models.DateField,
    models.DateTimeField,
)


# 文件字段类型
file_fields = (
    models.FileField,
    models.ImageField,
)


class ResolveConflictType(IntEnum):
    """
    解决冲突方案 0抛异常 1替换为冲突对象 2覆盖冲突对象 3忽略冲突
    """
    RAISE = 0
    REPLACE = 1
    COVER = 2
    IGNORE = 3


class RelationType(str, Enum):
    """
    关联类型，TO_CUSTOM 自定义  TO_ONE 关联单条记录  TO_MANY 关联多条记录
    """
    TO_CUSTOM = 'to_custom'
    TO_ONE = 'to_one'
    TO_MANY = 'to_many'


class FieldOption:
    """
    字段配置，配置字段的导入导出方法 依赖关系
    """

    default_rely_on = {
        RelationType.TO_CUSTOM: False,
        RelationType.TO_ONE: True,
        RelationType.TO_MANY: False,
    }

    def __init__(self, field_name, relation_type=None, **options):
        """初始化字段配置

        :param field_name: 字段名称
        :param relation_type: 关联类型
        :param options: 字段自定义选项
        """
        self.field_name = field_name
        self.relation_type = relation_type
        self.get = options.get('get', self.default_get)
        self.rely_on = options.get('rely_on', self.default_rely_on[self.relation_type])
        self.set = options.get('set', self.default_set)

    def default_get(self, obj):
        """默认导出方法

        :param obj: 数据对象
        :return: 字段值
        """
        if self.relation_type == RelationType.TO_ONE:
            return getattr(obj, self.field_name, None)
        elif self.relation_type == RelationType.TO_MANY:
            return getattr(obj, self.field_name).all()
        else:
            return None

    def default_set(self, obj, value):
        """默认导入方法

        :param obj: 数据对象
        :param value: 字段值
        """
        if self.relation_type == RelationType.TO_ONE:
            setattr(obj, self.field_name, value)
        elif self.relation_type == RelationType.TO_MANY:
            getattr(obj, self.field_name).add(*value)
        else:
            pass


class CheckOption:
    """
    字段检查配置，冲突检查和数据一致性检查
    """
    def __init__(self, **options):
        # 获取冲突对象方法
        self.get_conflict = options.get('get_conflict', self.default_get_conflict)
        # 解决冲突方案
        self.resolve_conflict_type = options.get('resolve_conflict_type', ResolveConflictType.COVER)
        # 冲突替换检查
        self.conflict_ignore_fields = options.get('conflict_ignore_fields', None)
        self.conflict_consistency_fields = options.get('conflict_consistency_fields', None)
        self.conflict_consistency_check = options.get('conflict_consistency_check',
                                                      self.default_conflict_consistency_check
                                                      if self.conflict_consistency_fields
                                                      else None)

    def default_get_conflict(self, obj):
        """默认获取冲突对象

        :param obj: 导入对象
        :return: 冲突对象
        """
        if hasattr(obj, resource_key_name):
            model = obj._meta.model
            model_manager = getattr(model, 'original_objects', model.objects)
            return model_manager.filter(**{resource_key_name: getattr(obj, resource_key_name)}).first()
        else:
            return None

    def default_conflict_consistency_check(self, obj, conflict_obj):
        """默认的冲突一致性检查

        :param obj: 导入对象
        :param conflict_obj: 冲突对象
        :return: 是否一致
        """
        for field_name in self.conflict_consistency_fields:
            if get_chain_attr(obj, field_name) != get_chain_attr(conflict_obj, field_name):
                return False
        return True


class DataOption:
    """
    数据处理配置
    """
    def __init__(self, model, **options):
        """数据处理配置初始化

        :param model: 模型类
        :param options: 自定义配置选项
        """
        # 资源表
        self.model = model
        # 所属的根资源表
        root_model = options.get('root', None)
        if root_model:
            try:
                root_model = try_import(root_model)
            except Exception:
                raise ResourceException('invalid root config %s' % options['root'])
        self.root_model = root_model
        if self.root_model:
            self.root_model._resource_meta.root_own.append(self)

        # 解析fields, pk不可移除
        fields_map = {field.name: field for field in self.model._meta.fields}
        field_names = getattr(options, 'fields', fields_map.keys())
        # 过滤不序列化的字段
        exclude_field_names = getattr(options, 'exclude_fields', ())
        serialize_field_names = set(field_names) - set(exclude_field_names)
        self.fields = [fields_map[field_name] for field_name in serialize_field_names]
        # 反序列化字段去除默认主键id, 如有需求再扩展
        deserialize_field_names = serialize_field_names - {'id'}
        self.data_fields = [fields_map[field_name] for field_name in deserialize_field_names]

        # 字段选项 key资源字段名称 value获取/设置该资源的方法
        self.field_options = {}
        for relation_type in RelationType.values():
            field_options = {}
            if relation_type in options:
                for field_name, field_option in options[relation_type].items():
                    field_options[field_name] = FieldOption(field_name, relation_type=relation_type, **field_option)
            setattr(self, relation_type, field_options)
            self.field_options.update(field_options)

        # 强制设置字段
        self.force = options.get('force', {})

        # 获取自定义关联文件
        self.get_files = options.get('files', None)

        # 检查选项
        self.check = CheckOption(**options.get('check', {}))

    @property
    def has_related(self):
        """是否有直接关联资源

        :return: bool
        """
        for relation_type in RelationType.values():
            if getattr(self, relation_type, None):
                return True
        return False

    def get_related(self, obj):
        """获取字段对应的关联资源

        :param obj: 数据对象
        :return: 字段对应的关联资源
        """
        related = {}
        for relation_type in RelationType.values():
            is_orm_related = relation_type in (RelationType.TO_ONE.value, RelationType.TO_MANY.value)
            for field_name, field_option in getattr(self, relation_type).items():
                res = field_option.get(obj)
                if is_orm_related:
                    if res and not isinstance(res, (Model, QuerySet, list)):
                        raise ResourceException('Unexcepted %s resource type: %s' % (relation_type, type(res)))

                    if isinstance(res, QuerySet):
                        res = list(res)

                related[field_name] = res

        return related


def try_import(cls):
    """如果是字符串尝试import

    :param cls: 可能对象
    :return: 对象
    """
    if isinstance(cls, str):
        return import_string(cls)
    return cls


def get_chain_attr(obj, attr_name_str):
    """获取属性

    :param obj: 数据对象
    :param attr_name_str: 链式字符串
    :return: 属性值
    """
    target = obj
    attr_names = attr_name_str.split('.')
    for attr_name in attr_names:
        if isinstance(target, Model):
            field = target._meta.model._resource_meta.valid_fields_map.get(attr_name)
            if field:
                target = get_serializable_value(obj, field)
            else:
                target = getattr(target, attr_name, None)
        else:
            target = getattr(target, attr_name, None)

    return target


def get_serializable_value(obj, field):
    """获取字段序列化值

    :param obj: 数据对象
    :param field: 字段
    :return: 序列化值
    """
    value = obj.serializable_value(field.attname)
    if isinstance(field, convert_string_fields):
        if value and not isinstance(value, str):
            value = field.value_to_string(obj)
    elif isinstance(field, file_fields):
        if value and not isinstance(value, str):
            value = value.name
    return value
