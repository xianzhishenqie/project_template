import copy
import logging
import os
import shutil

from django.conf import settings

from sv_base.utils.base.text import md5
from .exception import ResourceException
from .meta import ResolveConflictType, RelationType, convert_string_fields, file_fields, try_import


logger = logging.getLogger(__name__)


index_key = '_index'

project_file_dir_name = 'project_file'
root_file_dir_name = 'root_file'


class ModelResource:
    """
    从对象生成资源, 序列化导出数据 不需冲突检查
    """
    # 资源汇总池
    resource_pool = {}
    # 资源表对应的所有资源
    model_resources = {}
    p_key_pool = {}
    p_key_counter = 1

    def __new__(cls, obj, root_model):
        """生成对象资源实例

        :param obj: 数据对象
        :param root_model: 根资源表
        :return: 对象资源实例
        """
        # 序列化数据对象模型类
        p_model = pdumps(obj._meta.model)
        # 根据模型类和主键生成资源唯一标识
        resource_key = md5('%s:%s' % (p_model, obj.pk))
        # 资源池已有资源直接返回不再新建
        if resource_key in cls.p_key_pool:
            p_key = cls.p_key_pool[resource_key]
            resource = cls.resource_pool[p_key]
        else:
            resource = super(ModelResource, cls).__new__(cls)
            # 新建的资源加入资源池和资源表
            p_key = str(cls.p_key_counter)
            cls.p_key_counter += 1
            cls.p_key_pool[resource_key] = p_key
            cls.resource_pool[p_key] = resource
            cls.model_resources.setdefault(p_model, []).append(resource)

            # 预设置资源的模型和唯一标识
            resource.p_model = p_model
            resource.p_key = p_key
            # 预设置资源为未初始化
            resource._inited = False
        return resource

    # 重置类的资源池
    @classmethod
    def reset(cls):
        """重置类的资源池

        """
        cls.resource_pool = {}
        cls.model_resources = {}
        cls.p_key_pool = {}
        cls.p_key_counter = 1

    def __init__(self, obj, root_model):
        """初始化对象资源实例，实现需要防止对象重复初始化

        :param obj: 数据对象
        :param root_model: 根资源表
        """

        if self._inited:
            return

        # 初始化对象属性
        self.obj = obj
        self.model = obj._meta.model

        # 初始化对象关联属性
        self.root_own = obj._resource_meta.root_own
        self.root_model = self.model if self.root_own else root_model
        self.option = obj._resource_meta.get_option(self.root_model)

        # 初始化对象关联资源
        self.custom_related_resource = {}
        self.related_resources = []
        self.related_resource = {}
        self.related_rely_resources = []
        self.related_not_rely_resources = []

        # 初始化对象序列化数据
        self.data = None
        self.files = set()
        self._parsed = False
        self._rely_checked = False
        self._dumped = False

        # 标识资源已初始化
        self._inited = True

    def dumps(self):
        """序列化资源

        """
        # 只序列化一次资源
        if self._dumped:
            return

        # 初始化序列化数据的索引
        data = {index_key: {
            'model': self.p_model,
            'key': self.p_key,
        }}
        # 序列化数据
        for field in self.option.fields:
            data[field.attname] = self.get_field_serializable_value(field)
        self.data = data

        # 获取自定义文件
        if self.option.get_files:
            self.files.update(self.option.get_files(self.obj))

        # 标识资源已序列化
        self._dumped = True

    def get_relation_index(self):
        """获取关联数据索引

        :return: 关联数据索引
        """
        relation_index = {}
        for field_name, related_resrc in self.custom_related_resource.items():
            relation_index[field_name] = related_resrc

        for field_name, related_resrc in self.related_resource.items():
            if isinstance(related_resrc, list):
                relation_index[field_name] = [resrc.p_key for resrc in related_resrc]
            else:
                relation_index[field_name] = related_resrc.p_key if related_resrc else None
        return relation_index

    def get_field_serializable_value(self, field):
        """字段序列化

        :param field: 字段
        :return: 序列化值
        """
        obj = self.obj
        # 强置的字段直接设为强置值
        if field.attname in self.option.force:
            return self.option.force[field.attname]

        if isinstance(field, convert_string_fields):
            value = field.value_to_string(obj) if obj.serializable_value(field.attname) is not None else None
        # 文件字段解析出文件路径待处理
        elif isinstance(field, file_fields):
            real_file = obj.serializable_value(field.attname)
            value = real_file.name
            if value:
                # 准备复制文件
                self.files.add(real_file.path)
        else:
            value = obj.serializable_value(field.attname)
        return value

    def parse_related_tree(self):
        """递归解析资源的关联树

        """
        if self._parsed or not self.option.has_related:
            return

        self.get_related_resources()
        self._parsed = True

        for related_resource in self.related_resources:
            related_resource.parse_related_tree()

    def get_related_resources(self):
        """获取关联资源

        """
        if not self.option.has_related:
            return

        related = self.option.get_related(self.obj)
        for field_name, value in related.items():
            field_option = self.option.field_options[field_name]
            if field_option.relation_type == RelationType.TO_CUSTOM:
                self.custom_related_resource[field_name] = value
                continue

            if field_option.rely_on:
                collector = self.related_rely_resources
            else:
                collector = self.related_not_rely_resources

            if isinstance(value, list):
                field_related_resources = self.related_resource.setdefault(field_name, [])
                for obj in value:
                    sub_resource = type(self)(obj, self.root_model)
                    if sub_resource not in field_related_resources:
                        field_related_resources.append(sub_resource)
                    if sub_resource not in self.related_resources:
                        self.related_resources.append(sub_resource)
                        collector.append(sub_resource)
            else:
                sub_resource = type(self)(value, self.root_model) if value else None
                self.related_resource[field_name] = sub_resource
                if sub_resource and sub_resource not in self.related_resources:
                    self.related_resources.append(sub_resource)
                    collector.append(sub_resource)

    def check_circular_dependency(self, rely_chain=None, checking_list=None):
        """检查循环依赖

        :param rely_chain: 依赖链资源
        :param checking_list: 正在检查的资源列表
        """
        if not rely_chain and self._rely_checked:
            return

        if checking_list:
            if not rely_chain and self.p_key in checking_list:
                return
        else:
            checking_list = []
        checking_list.append(self.p_key)

        if rely_chain and self in rely_chain:
            raise ResourceException('resource[%s] rely on self' % self.obj.__dict__)

        for related_rely_resource in self.related_rely_resources:
            next_rely_chain = copy.copy(rely_chain) if rely_chain else set()
            next_rely_chain.add(self)
            related_rely_resource.check_circular_dependency(rely_chain=next_rely_chain, checking_list=checking_list)

        self._rely_checked = True
        checking_list.remove(self.p_key)

        for related_not_rely_resource in self.related_not_rely_resources:
            related_not_rely_resource.check_circular_dependency(checking_list=checking_list)

    @classmethod
    def copy_files(cls, tmp_dir, copying_files):
        """复制资源关联的文件

        :param tmp_dir: 目标临时目录
        :param copying_files: 文件对应列表
        """
        tmp_project_dir = os.path.join(tmp_dir, project_file_dir_name)
        tmp_root_dir = os.path.join(tmp_dir, root_file_dir_name)

        for src_file_path in copying_files:
            if not os.path.exists(src_file_path):
                continue

            if src_file_path.startswith(settings.BASE_DIR):
                related_file_path = src_file_path.replace(settings.BASE_DIR, '').lstrip('/')
                tmp_path = os.path.join(tmp_project_dir, related_file_path)
            else:
                tmp_path = os.path.join(tmp_root_dir, src_file_path.lstrip('/'))

            tmp_path_dir = os.path.dirname(tmp_path)
            if not os.path.exists(tmp_path_dir):
                os.makedirs(tmp_path_dir)

            logger.info('copy file [%s] to [%s]', src_file_path, tmp_path)
            try:
                shutil.copyfile(src_file_path, tmp_path)
            except Exception as e:
                logger.error('copy file [%s] to [%s] error: %s', src_file_path, tmp_path, e)
                continue


class DataResource:
    """从资源生成对象, 反序列化导入数据 需要冲突检查

    """

    resource_pool = {}
    model_resources = {}
    resource_index_pool = {}
    resource_data_pool = {}

    def __new__(cls, data, root_model):
        """生成序列化数据实例

        :param data: 序列化数据
        :param root_model: 根资源模型
        :return: 序列化数据实例
        """
        index = data[index_key]
        p_key = index['key']
        # 资源池已有资源直接返回不再新建
        if p_key in cls.resource_pool:
            resource = cls.resource_pool[p_key]
        else:
            resource = super(DataResource, cls).__new__(cls)
            # 新建的资源加入资源池和资源表
            cls.resource_pool[p_key] = resource
            cls.model_resources.setdefault(index['model'], []).append(resource)

            # 预设置资源的模型和唯一标识
            resource.p_model = index['model']
            resource.p_key = p_key
            # 预设置资源为未初始化
            resource._inited = False
        return resource

    def __init__(self, data, root_model):
        """初始化序列化数据实例，实现需要防止对象重复初始化

        :param data: 序列化数据
        :param root_model: 根资源模型
        """
        if self._inited:
            return

        self.data = data
        self.model = ploads(str(self.p_model))

        # 初始化对象关联属性
        self.root_own = self.model._resource_meta.root_own
        # TODO: 拥有的资源是根模型可能会导致问题
        self.root_model = self.model if self.root_own else root_model
        self.option = self.model._resource_meta.get_option(self.root_model)

        # 初始化对象关联资源
        self.related_index = self.resource_index_pool[self.p_key]

        self.custom_related_resource = {}
        self.related_resources = []
        self.related_resource = {}
        self.related_rely_resources = []
        self.related_not_rely_resources = []

        self.obj = None
        self._parsed = False
        self._rely_checked = False
        self._saved = False

        self._inited = True

    # 重置资源池
    @classmethod
    def reset(cls, resource_index_pool, resource_data_pool):
        """重置资源池

        :param resource_index_pool: 数据索引集合
        :param resource_data_pool: 数据集合
        """
        cls.resource_pool = {}
        cls.model_resources = {}
        cls.resource_index_pool = resource_index_pool
        cls.resource_data_pool = resource_data_pool

    @classmethod
    def parse_model(cls, data):
        """解析数据表模型

        :param data: 数据
        :return: 数据表模型
        """
        index = data[index_key]
        p_model = index['model']
        return ploads(str(p_model))

    def load_data(self):
        """载入数据，转换问数据实例

        """
        data = self.data
        obj = self.model()
        for field in self.option.data_fields:
            setattr(obj, field.attname, data[field.attname])
        self.obj = obj

    def load_related(self, rely_on=True):
        """载入关联数据

        :param rely_on: 过滤是否是依赖的数据
        """
        if not self.option.has_related:
            return

        for field_name, sub_data in self.custom_related_resource.items():
            field_option = self.option.field_options.get(field_name)
            if field_option.rely_on != rely_on or not field_option.set:
                continue

            field_option.set(self.obj, sub_data)

        for field_name, related_resource in self.related_resource.items():
            field_option = self.option.field_options.get(field_name)
            if field_option.rely_on != rely_on or not field_option.set:
                continue

            if isinstance(related_resource, list):
                related_obj = [resource.obj for resource in related_resource]
            else:
                related_obj = related_resource.obj if related_resource else None

            field_option.set(self.obj, related_obj)

    def save(self):
        """递归资源的关系导入数据

        """
        if self._saved:
            return

        # 先导入资源关联的依赖资源
        for related_rely_resource in self.related_rely_resources:
            if related_rely_resource:
                related_rely_resource.save()

        # 再导入资源本身
        logger.info('save resource[%s]', self.p_key)
        self.load_data()
        self.load_related(rely_on=True)
        self.obj = self.save_obj()
        self._saved = True
        # 再导入资源关联的非依赖资源
        for related_not_rely_resource in self.related_not_rely_resources:
            if related_not_rely_resource:
                related_not_rely_resource.save()
        self.load_related(rely_on=False)

    def save_obj(self):
        """保存数据对象

        """
        obj = self.obj
        check = self.option.check
        get_conflict = check.get_conflict
        if not get_conflict:
            obj.save()
            return obj

        conflict_obj = get_conflict(obj)
        if conflict_obj:
            # 冲突存在，抛异常
            if check.resolve_conflict_type == ResolveConflictType.RAISE:
                raise ResourceException('conflict obj exists!')
            # 替换为冲突对象检查(冲突对象可能不一致)
            elif check.resolve_conflict_type == ResolveConflictType.REPLACE:
                if check.conflict_consistency_check and not check.conflict_consistency_check(obj, conflict_obj):
                    # 冲突对象不一致时
                    logger.warning('obj[%s] replaced by conflict obj[%s], relation inconsistency!', obj.__dict__,
                                   conflict_obj.__dict__)
                return conflict_obj
            # 覆盖冲突对象检查(冲突对象可能不一致)
            elif check.resolve_conflict_type == ResolveConflictType.COVER:
                if check.conflict_consistency_check and not check.conflict_consistency_check(obj, conflict_obj):
                    tmp = copy.copy(obj.__dict__)
                    tmp.pop('id', None)
                    if check.conflict_ignore_fields:
                        for conflict_ignore_field in check.conflict_ignore_fields:
                            tmp.pop(conflict_ignore_field, None)
                    conflict_obj.__dict__.update(tmp)
                    conflict_obj.save()
                    logger.warning('obj[%s] cover conflict obj[%s], relation inconsistency!', obj.__dict__,
                                   conflict_obj.__dict__)
                return conflict_obj
            elif check.resolve_conflict_type == ResolveConflictType.IGNORE:
                obj.save()
        else:
            obj.save()

        return obj

    def parse_related_tree(self):
        """递归解析关联数据

        """
        if self._parsed or not self.option.has_related:
            return

        self.get_related_resources()
        self._parsed = True

        for related_resource in self.related_resources:
            related_resource.parse_related_tree()

    def get_related_resources(self):
        """获取关联的数据资源对象

        """
        for field_name, sub_index in self.related_index.items():
            field_option = self.option.field_options.get(field_name)
            if not field_option:
                continue

            if field_option.relation_type == RelationType.TO_CUSTOM:
                self.custom_related_resource[field_name] = sub_index
                continue

            if field_option.rely_on:
                collector = self.related_rely_resources
            else:
                collector = self.related_not_rely_resources

            if isinstance(sub_index, list):
                field_related_resources = self.related_resource.setdefault(field_name, [])
                for sub_key in sub_index:
                    sub_data = self.resource_data_pool[sub_key]
                    sub_resource = type(self)(sub_data, self.root_model)
                    if sub_resource not in field_related_resources:
                        field_related_resources.append(sub_resource)
                    if sub_resource not in self.related_resources:
                        self.related_resources.append(sub_resource)
                        collector.append(sub_resource)
            else:
                sub_data = self.resource_data_pool[sub_index] if sub_index else None
                sub_resource = type(self)(sub_data, self.root_model) if sub_data else None
                self.related_resource[field_name] = sub_resource
                if sub_resource and sub_resource not in self.related_resources:
                    self.related_resources.append(sub_resource)
                    collector.append(sub_resource)

    def check_circular_dependency(self, rely_chain=None, checking_list=None):
        """检查循环依赖

        :param rely_chain: 依赖链资源
        :param checking_list: 正在检查的资源列表
        """
        if not rely_chain and self._rely_checked:
            return

        if checking_list:
            if not rely_chain and self.p_key in checking_list:
                return
        else:
            checking_list = []
        checking_list.append(self.p_key)

        if rely_chain and self in rely_chain:
            raise ResourceException('resource[%s] rely on self' % self.data)

        for related_rely_resource in self.related_rely_resources:
            next_rely_chain = copy.copy(rely_chain) if rely_chain else set()
            next_rely_chain.add(self)
            related_rely_resource.check_circular_dependency(rely_chain=next_rely_chain, checking_list=checking_list)

        self._rely_checked = True
        checking_list.remove(self.p_key)

        for related_not_rely_resource in self.related_not_rely_resources:
            related_not_rely_resource.check_circular_dependency(checking_list=checking_list)

    @classmethod
    def _copy_files(cls, tmp_dir, dest_dir):
        """复制资源文件

        :param tmp_dir: 临时资源存放目录
        :param dest_dir: 目的资源存放目录
        """
        if not os.path.exists(tmp_dir):
            return

        pre_len = len(tmp_dir)
        for dirpath, dirnames, filenames in os.walk(tmp_dir):
            for filename in filenames:
                src_path = os.path.join(dirpath, filename)
                arcname = src_path[pre_len:].strip(os.path.sep)
                dst_path = os.path.join(dest_dir, arcname)
                logger.info('copy file [%s] to [%s]', src_path, dst_path)
                dst_dir = os.path.dirname(dst_path)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                try:
                    shutil.copyfile(src_path, dst_path)
                except Exception as e:
                    logger.error('copy file [%s] to [%s] error: %s', src_path, dst_path, e)

    @classmethod
    def copy_files(cls, tmp_dir):
        """复制资源文件

        :param tmp_dir: 临时资源存放目录
        """
        tmp_project_dir = os.path.join(tmp_dir, project_file_dir_name)
        cls._copy_files(tmp_project_dir, settings.BASE_DIR)

        tmp_root_dir = os.path.join(tmp_dir, root_file_dir_name)
        cls._copy_files(tmp_root_dir, '/')


def pdumps(obj):
    return f'{obj.__module__}.{obj.__name__}'


def ploads(obj_str):
    return try_import(obj_str)
