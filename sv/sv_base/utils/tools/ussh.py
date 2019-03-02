import os

import logging
import paramiko
from paramiko.sftp_client import SFTPClient

from typing import Optional


logging.getLogger('paramiko').setLevel(logging.WARNING)
logger = logging.getLogger('ssh')


class SSH:
    """
    ssh客户端
    """
    def __init__(self,
                 host: str,
                 port: int,
                 username: str,
                 password: Optional[str] = None,
                 key_path: Optional[str] = None) -> None:
        """ssh连接建立

        :param host: 目标地址
        :param port: 端口
        :param username: 用户名
        :param password: 密码
        :param key_path: key路径
        """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(host, port, username, password, key_filename=key_path)
        except paramiko.BadHostKeyException as e:
            logger.error("SSH HOST KEY ERROR %s - %s" % (host, e))
            raise e
        except paramiko.AuthenticationException as e:
            logger.error("SSH HOST AUTH FAILED %s - %s" % (host, e))
            raise e
        except paramiko.SSHException as e:
            logger.error("SSH TIMEOUT ERROR  %s - %s" % (host, e))
            raise e
        except Exception as e:
            logger.error("SSH ERROR %s - %s" % (host, e))
            raise e
        self.sftp = None

    def exe(self, command: str, timeout: int = 15, get_pty: bool = False, environment: Optional[dict] = None) -> tuple:
        """ssh执行命令

        :param command: 命令
        :param timeout: 超时时间
        :param get_pty: get_pty
        :param environment: 环境变量
        :return: 执行结果
        """
        try:
            stdin, stdout, stderr = self.client.exec_command(
                command, timeout=timeout, get_pty=get_pty, environment=environment)
            return stdin, stdout, stderr
        except paramiko.SSHException as e:
            logger.error("COMMAND EXEC ERROR %s" % e)
            raise e

    def upload(self, local_path: str, remote_path: str) -> None:
        """ssh上传文件

        :param local_path: 本地路径
        :param remote_path: 远程路径
        """
        self.sftp = self.client.open_sftp()
        try:
            self.sftp.put(local_path, remote_path)
            logger.debug("UPLOAD FILE SUCCESS upload %s to %s success", local_path, remote_path)
        except paramiko.SSHException as e:
            logger.error("UPLOAD FILE FAILED upload %s to %s failed - %s", local_path, remote_path, e)
            raise e

    @staticmethod
    def normalize_dir_path(dir_path: str) -> str:
        """标准化目录

        :param dir_path: 目录路径
        :return: 标准化目录路径
        """
        while dir_path.endswith("/"):
            dir_path = dir_path[:-1]
        return dir_path

    def upload_dir(self, local_path: str, remote_path: str, preserve_perm: bool = True) -> None:
        """ssh上传目录

        :param local_path: 本地路径
        :param remote_path: 远程路径
        :param preserve_perm: 是否开启权限保护
        """
        local_path = self.normalize_dir_path(local_path)
        remote_path = self.normalize_dir_path(remote_path)

        sftp = self.client.open_sftp()

        try:
            sftp.chdir(remote_path)
        except IOError:
            pass

        for root, dirs, fls in os.walk(local_path):
            prefix = os.path.commonprefix([local_path, root])
            suffix = root.split(prefix, 1)[1]
            if suffix.startswith("/"):
                suffix = suffix[1:]

            rem_root = os.path.join(remote_path, suffix)

            try:
                sftp.chdir(rem_root)
            except IOError:
                if preserve_perm:
                    mode = os.stat(root).st_mode & 0o0777
                else:
                    mode = 0o0777
                self.mkdir(sftp, rem_root, mode=mode, intermediate=True)
                sftp.chdir(rem_root)

            for f in fls:
                rem_file = os.path.join(rem_root, f)
                local_file = os.path.join(root, f)
                sftp.put(local_file, rem_file)
                if preserve_perm:
                    sftp.chmod(rem_file, os.stat(local_file).st_mode & 0o0777)

    def mkdir(self, sftp: SFTPClient, remote_path: str, mode: int = 0o0777, intermediate: bool = False) -> None:
        """ssh建目录

        :param sftp: sftp客户端
        :param remote_path: 远程目录路径
        :param mode: 创建模式
        :param intermediate: 失败前向尝试
        """
        remote_path = self.normalize_dir_path(remote_path)
        if intermediate:
            try:
                sftp.mkdir(remote_path, mode=mode)
            except IOError:
                self.mkdir(sftp, remote_path.rsplit("/", 1)[0], mode=mode,
                           intermediate=True)
                return sftp.mkdir(remote_path, mode=mode)
        else:
            sftp.mkdir(remote_path, mode=mode)

    def close(self) -> None:
        """关闭客户端连接

        """
        self.client.close()


ssh = SSH
