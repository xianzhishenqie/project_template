import os
import time


def timestamp_to_time(timestamp):
    time_struct = time.localtime(timestamp)
    return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)


def get_file_size(file_path):
    """
        获取文件的大小
    :param file_path:   文件路径
    :return:    文件大小
    """
    size = os.path.getsize(file_path)
    size = size / float(1024 * 1024)
    return round(size, 2)


def get_file_create_time(file_path):
    """
        获取文件的创建时间
    :param file_path:   文件路径
    :return:    文件创建的时间
    """
    t = os.path.getctime(file_path)
    return timestamp_to_time(t)


def get_file_modify_time(file_path):
    """
        获取文件的修改时间
    :param file_path:   文件路径
    :return:    文件修改的时间
    """
    t = os.path.getmtime(file_path)
    return timestamp_to_time(t)
