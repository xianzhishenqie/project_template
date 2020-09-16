import os
import logging
import time

from django.conf import settings
from django.db.models import Model

from sv_base.utils.base.thread import async_exe
from sv_base.utils.base.cache import CacheProduct, func_cache
from sv_base.extensions.db.decorators import promise_db_connection

logger = logging.getLogger(__name__)

common_cache = CacheProduct("base_common_cache")


def _get_obj_key(func, pk_or_obj, model=None):
    if isinstance(pk_or_obj, Model):
        key = None
    else:
        if not model:
            return None

        key = "__name__%s_model_%s" % (pk_or_obj, model)

    return key


@func_cache(common_cache, key_func=_get_obj_key)
def get_obj(pk_or_obj, model=None):
    """根据主键或对象本身获取model对象

    :param pk_or_obj: 主键或对象本身
    :param model: model类
    :return: model对象
    """
    if not pk_or_obj:
        return None

    if isinstance(pk_or_obj, Model):
        obj = pk_or_obj
    else:
        if not model:
            return None

        obj = model.objects.get(pk=pk_or_obj)

    return obj


def clear_nouse_field_file(using_queryset, file_field_name):
    """清除不再使用的关联文件

    :param using_queryset: 使用中的数据querySet
    :param file_field_name: 关联的文件字段名
    :return: None
    """
    # 获取文件所在目录
    file_dir_name = getattr(using_queryset.model, file_field_name).field.get_directory_name()
    file_dir = os.path.join(settings.MEDIA_ROOT, file_dir_name)
    if not os.path.exists(file_dir):
        return

    # 使用中的文件列表
    all_filenames = os.listdir(file_dir)
    using_filenames = []
    for instance in using_queryset:
        instance_file = getattr(instance, file_field_name)
        if instance_file:
            using_filenames.append(os.path.basename(instance_file.name))

    # 清除不再使用的关联文件
    nouse_filenames = list(set(all_filenames) - set(using_filenames))
    for filename in nouse_filenames:
        file_path = os.path.join(file_dir, filename)
        os.remove(file_path)
        print('remove file: %s' % file_path)


class BulkSaver:
    """
    延迟批量创建、更新，实时性要求不高的数据保存
    """

    def __init__(self, batch_size=1000, delay=0, create_failed=None, update_failed=None):
        self.batch_size = batch_size
        self.delay = delay
        self.create_failed = create_failed
        self.update_failed = update_failed

        self.create_pool = {}
        self.create_receiving = False

        self.update_pool = {}
        self.update_receiving = False

    def create(self, objs, delay=None):
        if not objs:
            return

        self._add_objs(objs, self.create_pool)

        if self.create_receiving:
            return

        self.create_receiving = True

        delay = delay if delay is not None else self.delay

        def _create():
            if delay:
                time.sleep(delay)

            creating_pool = self.create_pool
            self.create_pool = {}
            self.create_receiving = False
            self._create(creating_pool)

        if delay:
            async_exe(_create)
        else:
            _create()

    def update(self, objs, delay=None):
        if not objs:
            return

        self._add_objs(objs, self.update_pool)

        if self.update_receiving:
            return

        self.update_receiving = True

        delay = delay if delay is not None else self.delay

        def _update():
            if delay:
                time.sleep(delay)

            updating_pool = self.update_pool
            self.update_pool = {}
            self.update_receiving = False
            self._update(updating_pool)

        if delay:
            async_exe(_update)
        else:
            _update()

    @promise_db_connection
    def _create(self, pool):
        for model, obj_mapping in pool.items():
            objs = list(obj_mapping.values())
            try:
                model.objects.bulk_create(objs, batch_size=self.batch_size)
            except Exception as e:
                logger.error(f'bulk create {model.__name__} objs failed: {e}')
                if self.create_failed:
                    self.create_failed(model, objs, e)

    @promise_db_connection
    def _update(self, pool):
        for model, obj_mapping in pool.items():
            objs = list(obj_mapping.values())
            fields = [field.name for field in model._meta.fields if not field.primary_key]
            try:
                model.objects.bulk_update(objs, fields=fields, batch_size=self.batch_size)
            except Exception as e:
                logger.error(f'bulk update {model.__name__} objs failed: {e}')
                if self.update_failed:
                    self.update_failed(model, objs, e)

    def _add_objs(self, objs, pool):
        if not objs:
            return

        if isinstance(objs, Model):
            objs = [objs]

        for obj in objs:
            model = obj._meta.model
            obj_key = f'{model.__name__}:{obj.pk}'
            pool.setdefault(model, {})[obj_key] = obj
