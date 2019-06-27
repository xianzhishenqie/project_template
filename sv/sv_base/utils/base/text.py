import hashlib
import os
import re
import uuid

from django.conf import settings


def ec(t):
    """默认编码字符串

    :param t: 字符串
    :return: 字节
    """
    return t.encode(settings.ENCODING) if isinstance(t, str) else t


def dc(t):
    """默认解码字节

    :param t: 字节
    :return: 字符串
    """
    return t.decode(settings.ENCODING) if isinstance(t, bytes) else t


def md5(t):
    """默认md5

    :param t: 字符串
    :return: md5值
    """
    return hashlib.md5(ec(t)).hexdigest()


def sha1(t):
    """默认sha1

    :param t: 字符串
    :return: sha1值
    """
    return hashlib.sha1(ec(t)).hexdigest()


def rk():
    """默认随机唯一字符串

    :return: 随机唯一字符串
    """
    return md5(str(uuid.uuid4()))


def rk_filename(filename):
    """默认随机文件名

    :param filename: 原始文件名
    :return: 随机文件名
    """
    return rk() + os.path.splitext(filename)[-1]


# 中文字符
zh_pattern = re.compile('[\u4e00-\u9fa5]+')


def contain_zh(word):
    """字符串是否包含中文

    :param word: 字符串
    :return: 搜索结果
    """
    match = zh_pattern.search(word)

    return match
