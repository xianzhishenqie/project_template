import logging
import os
import subprocess
from typing import List

from sv_base.utils.base.text import rk


logger = logging.getLogger(__name__)


def get_usb_devices() -> List[str]:
    """获取usb设备列表

    :return: usb设备列表
    """
    usb_devices = []
    with open('/proc/partitions') as partitionsFile:
        lines = partitionsFile.readlines()[2:]
        for line in lines:
            words = [x.strip() for x in line.split()]
            minor_number = int(words[1])
            device_name = words[3]
            if minor_number % 16 == 0:
                path = '/sys/class/block/' + device_name
                if os.path.islink(path):
                    if os.path.realpath(path).find('/usb') > 0:
                        usb_devices.append('/dev/%s' % device_name)
    return usb_devices


def mount_device(device: str) -> str:
    """挂载usb设备

    :param device: usb设备
    :return: 挂载路径
    """
    key = rk()
    mount_path = '/mnt/%s' % key
    mount_cmd = 'mount %s %s' % (device, mount_path)
    logger.info(mount_cmd)
    os.makedirs(mount_path)
    subprocess.call(mount_cmd, shell=True)
    return mount_path


def umount_device(mount_path: str) -> None:
    """卸载usb设备

    :param mount_path: usb设备挂载路径
    :return: None
    """
    umount_cmd = 'umount %s' % mount_path
    logger.info(umount_cmd)
    subprocess.call(umount_cmd, shell=True)
    os.removedirs(mount_path)


class usb:
    """
    使用usb设备类
    """
    def __enter__(self):
        usb_devices = get_usb_devices()
        self.mount_paths = []
        for usb_device in usb_devices:
            mount_path = mount_device(usb_device)
            self.mount_paths.append(mount_path)
        return self.mount_paths

    def __exit__(self, exc_type, exc_val, exc_tb):
        for mount_path in self.mount_paths:
            umount_device(mount_path)
