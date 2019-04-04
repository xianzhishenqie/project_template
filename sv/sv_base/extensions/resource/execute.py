import logging

from django.db import transaction
from django.db.models import QuerySet

from .resource import ModelResource, DataResource


logger = logging.getLogger(__name__)


class Dumper:
    def __init__(self, root_objs):
        # 根资源
        if isinstance(root_objs, (tuple, list, QuerySet)):
            self.root_objs = root_objs
        else:
            self.root_objs = [root_objs]
        # 生成资源类
        self.model_resource_class = type('ModelResource', (ModelResource,), {})

        # 初始化根资源索引
        self.resource_root = []
        # 初始化资源关联关系索引
        self.resource_index = {}
        # 初始化资源数据
        self.resource_data = {}
        # 初始化资源关联文件
        self.files = set()

    def dumps(self, dest_dir=None):
        self.model_resource_class.reset()

        for obj in self.root_objs:
            root_resource = self.model_resource_class(obj, obj._meta.model)
            self.resource_root.append(root_resource.p_key)
            # 解析根资源的资源关联树, 注满资源池
            root_resource.parse_related_tree()
            root_resource.check_circular_dependency()

        # 序列化资源池资源，设置关联关系索引，资源数据，关联文件
        for key, resource in self.model_resource_class.resource_pool.items():
            resource.dumps()
            self.resource_index[key] = resource.get_relation_index()
            self.resource_data[key] = resource.data
            self.files.update(resource.files)

        # 复制资源关联文件
        if dest_dir and self.files:
            self.model_resource_class.copy_files(dest_dir, list(self.files))

        return {
            'root': self.resource_root,
            'index': self.resource_index,
            'data': self.resource_data,
            'files': self.files,
        }


class Loader:
    def __init__(self):
        # 生成资源类
        self.data_resource_class = type('DataResource', (DataResource,), {})

    def loads(self, data, src_dir=None):
        resource_root = data['root']
        resource_index = data['index']
        resource_data = data['data']

        self.data_resource_class.reset(resource_index, resource_data)

        # 从根资源解析资源树
        root_resources = []
        for root_key in resource_root:
            root_data = resource_data[root_key]
            root_model = self.data_resource_class.parse_model(root_data)
            resource = self.data_resource_class(root_data, root_model)
            resource.parse_related_tree()
            resource.check_circular_dependency()
            root_resources.append(resource)

        # 从根资源开始递归导入数据
        with transaction.atomic():
            for root_resource in root_resources:
                logger.info('save root resource[%s] start', root_resource.p_key)
                root_resource.save()
                logger.info('save root resource[%s] end', root_resource.p_key)

        # 复制资源关联文件
        if src_dir:
            self.data_resource_class.copy_files(src_dir)
