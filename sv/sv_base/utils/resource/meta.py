from enum import IntEnum, Enum

from django.db import models
from django.db.models import Model, QuerySet
from django.utils.module_loading import import_string
from django.utils import six

from .exception import ResourceException


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


# 解决冲突方案 0抛异常 1替换为冲突对象 2覆盖冲突对象 3忽略冲突
class ResolveConflictType(IntEnum):
    RAISE = 0
    REPLACE = 1
    COVER = 2
    IGNORE = 3


class RelationType(str, Enum):
    TO_CUSTOM = 'to_custom'
    TO_ONE = 'to_one'
    TO_MANY = 'to_many'


class FieldOption:
    def __init__(self, field_name, relation_type=None, **options):
        self.field_name = field_name
        self.relation_type = relation_type
        self.get = options.get('get', self.default_get)
        self.rely_on = options.get('rely_on', True)
        self.set = options.get('set', self.default_set)

    def default_get(self, obj):
        if self.relation_type == RelationType.TO_ONE:
            return getattr(obj, self.field_name, None)
        elif self.relation_type == RelationType.TO_MANY:
            return getattr(obj, self.field_name).all()
        else:
            return None

    def default_set(self, obj, value):
        if self.relation_type == RelationType.TO_ONE:
            setattr(obj, self.field_name, value)
        elif self.relation_type == RelationType.TO_MANY:
            getattr(obj, self.field_name).add(*value)
        else:
            pass


class CheckOption:
    def __init__(self, **options):
        # 获取冲突对象方法
        self.get_conflict = options.get('get_conflict', self.default_get_conflict)
        # 解决冲突方案
        self.resolve_conflict_type = options.get('resolve_conflict_type', ResolveConflictType.COVER)
        # 冲突替换检查
        self.conflict_ignore_fields = options.get('conflict_ignore_fields', None)
        self.conflict_consistency_fields = options.get('conflict_consistency_fields', None)
        self.conflict_consistency_check = options.get('conflict_consistency_check', self.default_conflict_consistency_check if self.conflict_consistency_fields else None)

    def default_get_conflict(self, obj):
        if hasattr(obj, resource_key_name):
            model = obj._meta.model
            model_manager = getattr(model, 'original_objects', model.objects)
            return model_manager.filter(**{resource_key_name: getattr(obj, resource_key_name)}).first()
        else:
            return None

    def default_conflict_consistency_check(self, obj, conflict_obj):
        for field_name in self.conflict_consistency_fields:
            if get_chain_attr(obj, field_name) != get_chain_attr(conflict_obj, field_name):
                return False
        return True


# 字段选项
class DataOption:
    def __init__(self, model, **options):
        # 资源表
        self.model = model
        # 所属的根资源表
        root_model = options.get('root', None)
        if root_model:
            try:
                root_model = try_import(root_model)
            except:
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
        for relation_type in RelationType.__members__.values():
            field_options = {}
            if relation_type in options:
                for field_name, field_option in options[relation_type].items():
                    field_options[field_name] = FieldOption(field_name, relation_type=relation_type, **field_option)
            setattr(self, relation_type, field_options)
            self.field_options.update(field_options)

        # 强制设置字段
        self.force = options.get('force', {})

        # 检查选项
        self.check = CheckOption(**options.get('check', {}))

    @property
    def has_related(self):
        for relation_type in (RelationType.TO_ONE, RelationType.TO_MANY):
            if getattr(self, relation_type):
                return True
        return False

    def get_related(self, obj):
        related = {}
        for relation_type in (RelationType.TO_ONE, RelationType.TO_MANY):
            for field_name, field_option in getattr(self, relation_type).items():
                res = field_option.get(obj)
                if res and not isinstance(res, (Model, QuerySet)):
                    raise ResourceException('Unexcepted %s resource type: %s' % (relation_type, type(res)))

                if isinstance(res, QuerySet):
                    res = list(res)

                related[field_name] = res

        return related


class ResourceOption:
    def __init__(self, cls, resource=None):
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

    # 根资源表的唯一映射, 表名
    @classmethod
    def generate_root_model_key(cls, root_model=None):
        return root_model._meta.db_table if root_model else '_default'

    # 父资源表的唯一映射, 表名
    @classmethod
    def generate_root_parent_model_key(cls, root_model, parent_model):
        return '%s:%s' % (root_model._meta.db_table, parent_model._meta.db_table)

    def set_option(self, data_option):
        root_model_key = self.generate_root_model_key(data_option.root_model)
        self.options[root_model_key] = data_option

    def get_option(self, root_model=None):
        root_model_key = self.generate_root_model_key(root_model)
        option = self.options.get(root_model_key, None)
        # 如果根据根资源表找不到对应的拥有资源，寻找默认的拥有资源
        if root_model and not option:
            option = self.options.get(self.generate_root_model_key(), None)
        return option


# 如果是字符串尝试import
def try_import(cls):
    if isinstance(cls, six.string_types):
        return import_string(cls)
    return cls


def get_chain_attr(obj, attr_name_str):
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
    value = obj.serializable_value(field.attname)
    if isinstance(field, convert_string_fields):
        if value and not isinstance(value, six.string_types):
            value = field.value_to_string(obj)
    elif isinstance(field, file_fields):
        if value and not isinstance(value, six.string_types):
            value = value.name
    return value
