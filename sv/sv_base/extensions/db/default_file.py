import logging
import os

from django.db import transaction

from sv_base.utils.tools.file import FileClient
from sv_base.models import DefaultFile

logger = logging.getLogger(__name__)


def add_default_files(group, file_mapping):
    """
    添加默认文件
    :param group: 组
    :param file_mapping: 文件名称路径映射
    :return: 默认文件列表
    """
    exist_default_files = DefaultFile.objects.filter(group=group)
    exist_name_mapping = {default_file.name: default_file for default_file in exist_default_files}

    file_client = FileClient()
    default_files = []
    saving_default_files = set()
    saved_remote_files = set()
    try:
        for i, (name, file_path) in enumerate(file_mapping.items()):
            seq = i + 1
            mtime = str(os.path.getmtime(file_path))
            if name in exist_name_mapping:
                # 存在的默认文件
                default_file = exist_name_mapping.pop(name)
                default_files.append(default_file)
                # 序号有变化, 更新
                if seq != default_file.seq:
                    default_file.seq = seq
                    saving_default_files.add(default_file)

                # 文件有变化, 更新
                if file_path != default_file.local_file or mtime != default_file.mtime:
                    remote_file = file_client.upload(file_path)
                    if not remote_file:
                        raise Exception('upload default file failed')
                    saved_remote_files.add(remote_file)

                    default_file.seq = seq
                    default_file.local_file = file_path
                    default_file.mtime = mtime
                    default_file.remote_file = remote_file
                    saving_default_files.add(default_file)
            else:
                # 不存在的文件需要新增上传
                remote_file = file_client.upload(file_path)
                if not remote_file:
                    raise Exception('upload default file failed')
                saved_remote_files.add(remote_file)

                default_file = DefaultFile(
                    group=group,
                    name=name,
                    seq=seq,
                    local_file=file_path,
                    mtime=mtime,
                    remote_file=remote_file,
                )
                default_files.append(default_file)
                saving_default_files.add(default_file)
    except Exception:
        _remove_remote_files(file_client, saved_remote_files)
        raise

    try:
        with transaction.atomic():
            # 没有对应的文件需要删掉
            for default_file in exist_name_mapping.values():
                default_file.delete()

            for default_file in saving_default_files:
                default_file.save()
    except Exception as e:
        logger.error('save default file error: %s', e)
        _remove_remote_files(file_client, saved_remote_files)
        raise

    return [_serialize_default_file(default_file) for default_file in default_files]


def _remove_remote_files(file_client, remote_files):
    for remote_file in remote_files:
        try:
            file_client.delete(remote_file)
        except Exception:
            pass


def get_default_files(group):
    """
    获取默认文件
    :param group: 组
    :return: 默认文件列表
    """
    default_files = DefaultFile.objects.filter(group=group).order_by('seq')
    return [_serialize_default_file(default_file) for default_file in default_files]


def is_valid_default_file(group, file):
    """
    是否是有效的默认文件
    :param group: 组
    :param file: 文件id
    :return: 是否已存在默认文件
    """
    return DefaultFile.objects.filter(group=group, remote_file=file).exists()


def _serialize_default_file(default_file):
    """
    序列化默认文件
    :param default_file: 默认文件
    :return: 默认文件数据
    """
    return {
        'name': default_file.name,
        'file': default_file.remote_file,
        'file_url': default_file.remote_file.url,
    }
