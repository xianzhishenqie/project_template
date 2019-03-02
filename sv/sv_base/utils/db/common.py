import os
from typing import Optional, Union, Type

from django.conf import settings
from django.db import connections
from django.db.models import Model, QuerySet


def close_old_connections() -> None:
    """清除未使用的和废弃的连接

    """
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()


def get_obj(pk_or_obj: Union[str, int, Model, None], model: Type[Model]) -> Optional[Model]:
    """根据主键或对象本身获取model对象

    :param pk_or_obj: 主键或对象本身
    :param model: model类
    :return: model对象
    """
    if not pk_or_obj:
        return None

    if isinstance(pk_or_obj, model):
        obj = pk_or_obj
    else:
        obj = model.objects.get(pk=pk_or_obj)

    return obj


def clear_nouse_field_file(using_queryset: QuerySet, file_field_name: str) -> None:
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
