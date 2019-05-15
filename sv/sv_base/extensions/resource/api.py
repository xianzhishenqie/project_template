import base64
import json
import os
import pyminizip
import shutil
import zlib

from django.utils import timezone

from sv_base import app_settings
from sv_base.utils.base.text import rk
from sv_base.utils.tools.dir import list_files

from .exception import ResourceException
from .execute import Dumper, Loader


def dump_resource_data(resource_data):
    """序列化资源数据

    :param resource_data: 资源数据
    :return: 序列化的资源数据
    """
    data = {
        'root': resource_data['root'],
        'index': resource_data['index'],
        'data': resource_data['data'],
    }

    data_str = json.dumps(data, ensure_ascii=False)
    data_str = zlib.compress(data_str)
    data_str = base64.b64encode(data_str)
    return data_str


def load_resource_data(data_str):
    """解析资源数据

    :param data_str: 序列化的资源数据
    :return: 资源数据
    """
    data_str = base64.b64decode(data_str)
    data_str = zlib.decompress(data_str)
    data = json.loads(data_str)
    return data


def random_filename():
    """随机文件名

    :return: 随机文件名
    """
    return '{}-{}'.format(timezone.now().strftime('%Y%m%d%H%M%S'), rk())


class ResourceHandler(object):
    """
    资源处理类
    """

    # 资源导出的文件名
    data_file_name = 'data'

    def __init__(self, **kwargs):
        self.dump_resource_data = kwargs.get('dump_resource_data', dump_resource_data)
        self.load_resource_data = kwargs.get('load_resource_data', load_resource_data)

        self.extra_export_handle = kwargs.get('extra_export_handle')
        self.extra_import_handle = kwargs.get('extra_import_handle')

    @classmethod
    def prepare_tmp_dir(cls, filename=None):
        """准备临时目录

        :param filename: 目录名称
        :return: 临时目录
        """
        filename = filename or random_filename()
        tmp_dir = os.path.join(app_settings.RESOURCE_TMP_DIR, filename)
        os.makedirs(tmp_dir)
        return tmp_dir

    def dumps(self, root_objs, tmp_dir):
        """导出数据

        :param root_objs: 根数据对象集合
        :param tmp_dir: 临时目录
        :return: 序列化数据
        """
        data = Dumper(root_objs).dumps(tmp_dir)
        data_str = self.dump_resource_data(data)
        with open(os.path.join(tmp_dir, self.data_file_name), 'w') as data_file:
            data_file.write(data_str)

        return data_str

    def loads(self, tmp_dir):
        """导入数据

        :param tmp_dir: 临时目录
        :return: 解析的数据
        """
        data_file_path = os.path.join(tmp_dir, self.data_file_name)
        if os.path.exists(data_file_path):
            with open(data_file_path, 'r') as data_file:
                data_str = data_file.read()
                data = self.load_resource_data(data_str)
            Loader().loads(data, tmp_dir)
        else:
            raise ResourceException('invalid package: no data file found')

        return data

    @classmethod
    def pack_zip(cls, tmp_dir, password=None):
        """zip导出

        :param tmp_dir: 临时目录
        :param password: 打包密码
        :return: zip导出文件路径
        """
        zip_file_path = '{}.zip'.format(tmp_dir)
        files = list_files(tmp_dir, True)
        file_prefixs = []
        for file_path in files:
            file_dir = os.path.dirname(file_path)
            file_prefix = file_dir.replace(tmp_dir, '') or '/'
            file_prefixs.append(file_prefix)

        pyminizip.compress_multiple(
            files,
            file_prefixs,
            zip_file_path,
            password,
            5,
        )

        return zip_file_path

    @classmethod
    def unpack_zip(cls, zip_file_path, tmp_dir, password=None):
        """解压zip文件

        :param zip_file_path: zip文件路径
        :param tmp_dir: 临时解压路径
        :param password: 解压密码
        """
        pyminizip.uncompress(zip_file_path, password, tmp_dir, False)

    def export_package(self, root_objs, filename=None, password=None):
        """导出数据

        :param root_objs: 根数据对象集合
        :param filename: 文件名称
        :param password: 文件密码
        :return: 文件路径
        """
        tmp_dir = self.prepare_tmp_dir(filename=filename)

        try:
            self.dumps(root_objs, tmp_dir)
            if self.extra_export_handle:
                self.extra_export_handle(root_objs, tmp_dir)
            zip_file_path = self.pack_zip(tmp_dir, password=password)
        finally:
            shutil.rmtree(tmp_dir)

        return zip_file_path

    def import_package(self, package_file, password=None):
        """导入数据

        :param package_file: 数据文件
        :param password: 数据密码
        """
        tmp_dir = self.prepare_tmp_dir()

        try:
            self.unpack_zip(package_file, tmp_dir, password=password)
            if self.extra_import_handle:
                self.extra_import_handle(tmp_dir)
            self.loads(tmp_dir)
        finally:
            shutil.rmtree(tmp_dir)
