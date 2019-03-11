from typing import Optional, Union

from django.db.models import QuerySet

from .config import Resource
from .execute import Dumper, Loader
from .meta import ResolveConflictType, RelationType


def dumps(root_objs: Union[QuerySet, list], to_dir: Optional[str] = None) -> dict:
    """ 导出数据

    :param root_objs: 数据列表
    :param to_dir: 关联文件导出路径
    :return: 序列化数据
    """
    return Dumper(root_objs).dumps(to_dir)


def loads(root: list, index: dict, data: dict, from_dir: Optional[str] = None) -> None:
    """导入数据

    :param root: 根数据索引
    :param index: 数据索引
    :param data: 数据
    :param from_dir: 关联文件路径
    """
    return Loader().loads(root, index, data, from_dir)
