import logging
from io import BytesIO

from fdfs_client.client import Fdfs_client
from django.conf import settings

from sv_base.utils.base.property import cached_property
from sv_base.utils.base.text import dc, ec, rk
from sv_base.utils.tools.dir import get_file_suffix

logger = logging.getLogger(__name__)


class FileClient:
    """
    文件客户端 fdfs
    """

    def __init__(self, hosts=settings.FDFS_TRACKER_HOST, port=settings.FDFS_TRACKER_PORT, timeout=5,
                 name='Tracker Pool'):
        """
        初始化客户端参数
        :param hosts: tracker主机地址
        :param port: tracker端口
        :param timeout: 连接超时时间
        :param name: 连接池名称
        """
        if isinstance(hosts, str):
            hosts = (hosts,)
        else:
            hosts = tuple(hosts)

        self.config = {
            'host_tuple': hosts,
            'port': port,
            'timeout': timeout,
            'name': name,
        }

    @cached_property
    def client(self):
        return Fdfs_client(self.config)

    def upload(self, filename=None, content=None, file_ext_name=None):
        """
        上传文件
        :param filename: 本地文件路径
        :param content: 文件内容
        :param file_ext_name: 文件后缀
        :return: 远程文件id
        """
        ret = None
        if filename:
            try:
                ret = self.client.upload_by_filename(filename)
            except Exception as e:
                logger.error('[FDFS]upload file[%s] error: %s', filename, e)
        elif content:
            try:
                ret = self.client.upload_by_buffer(content, file_ext_name=file_ext_name)
            except Exception as e:
                logger.error('[FDFS]upload file with content error: %s', e)

        if ret:
            file_id = dc(ret['Remote file_id'])
        else:
            file_id = None

        return file_id

    def download(self, file_id, filename=None):
        """
        下载文件file_id
        :param file_id: 远程文件id
        :param filename: 下载到本地文件路径
        :return: filename不为空无返回，为空返回buffer
        """
        if filename:
            try:
                self.client.download_to_file(filename, ec(file_id))
            except Exception as e:
                logger.error('[FDFS]download file[%s] to [%s] error: %s', file_id, filename, e)
                return False
            else:
                return True
        else:
            try:
                ret = self.client.download_to_buffer(ec(file_id))
            except Exception as e:
                logger.error('[FDFS]download file[%s] error: %s', file_id, e)
                return None
            else:
                return ret['Content']

    def download_as_memory_file(self, file_id):
        """
        下载到内存文件
        :param file_id: 远程文件id
        :return: 内存文件
        """
        buffer = self.download(file_id)
        if buffer:
            memory_file = BytesIO()
            memory_file.write(buffer)
            memory_file.seek(0)
        else:
            memory_file = None

        return memory_file

    def download_as_tmp_file(self, file_id):
        """
        下载到临时文件
        :param file_id: 远程文件id
        :return: 临时文件路径
        """
        suffix = get_file_suffix(file_id)
        tmp_file_name = f'/tmp/{rk()}.{suffix}'
        if self.download(file_id, tmp_file_name):
            return tmp_file_name
        else:
            return None

    def delete(self, file_id):
        """
        删除远程文件
        :param file_id: 远程文件id
        :return: 无
        """
        try:
            self.client.delete_file(ec(file_id))
        except Exception as e:
            logger.error('[FDFS]delete file[%s] error: %s', file_id, e)
            return False
        else:
            return True

    @classmethod
    def url(cls, file_id):
        """
        获取远程文件地址
        :param file_id: 远程文件id
        :return: 远程文件地址
        """
        return f'{settings.FDFS_SERVER}/{file_id}'
