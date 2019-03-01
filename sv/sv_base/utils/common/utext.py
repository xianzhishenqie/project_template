from __future__ import annotations

import hashlib
import os
import re
import uuid

from typing import Optional

from django.conf import settings
from django.utils.encoding import force_text


def ec(t: str) -> bytes:
    """默认编码字符串

    :param t: 字符串
    :return: 字节
    """
    return t.encode(settings.ENCODING)


def dc(t: bytes) -> str:
    """默认解码字节

    :param t: 字节
    :return: 字符串
    """
    return t.decode(settings.ENCODING)


def md5(t: str) -> str:
    """默认md5

    :param t: 字符串
    :return: md5值
    """
    return hashlib.md5(ec(t)).hexdigest()


def sha1(t: str) -> str:
    """默认sha1

    :param t: 字符串
    :return: sha1值
    """
    return hashlib.sha1(ec(t)).hexdigest()


def rk() -> str:
    """默认随机唯一字符串

    :return: 随机唯一字符串
    """
    return md5(str(uuid.uuid4()))


def rk_filename(filename: str) -> str:
    """默认随机文件名

    :param filename: 原始文件名
    :return: 随机文件名
    """
    return rk() + os.path.splitext(filename)[-1]


# 中文字符
zh_pattern = re.compile('[\u4e00-\u9fa5]+')


def contain_zh(word: str) -> object:
    """字符串是否包含中文

    :param word: 字符串
    :return: 搜索结果
    """
    match = zh_pattern.search(word)

    return match


class Txt(str):
    """
    自定义的字符串类
    """
    pass


class Trans(Txt):
    """
    国际化字符串类
    """
    # 收集所有的国际化字符串
    source = set()

    code = None

    # 格式化参数
    p = None

    def __new__(cls, s: str, code: Optional[int, str] = None) -> object:
        """生成初始化实例对象

        :param s: 国际化字符串
        :param code: 国际化字符串标识码
        :return: 实例对象
        """
        txt = force_text(s)
        self = super(Trans, cls).__new__(cls, txt)
        # 国际化字符串
        self.txt = txt
        # 标识码
        self.code = code
        # 收集
        cls.source.add(self)
        return self

    def __call__(self, **kwargs) -> Trans:
        """载入格式化参数

        :param kwargs: 格式化参数
        :return: self
        """
        self.p = kwargs
        return self

    def __eq__(self, other: Trans) -> bool:
        """通过code比较是否相等

        :param other: 其他国际化字符串
        :return: bool
        """
        r = super(Trans, self).__eq__(other)
        try:
            return r and self.code == other.code
        except AttributeError:
            return r

    def __ne__(self, other: Trans) -> bool:
        """通过code比较不相等

        :param other: 其他国际化字符串
        :return: bool
        """
        return not self.__eq__(other)

    def __hash__(self, *args, **kwargs) -> int:
        return hash(self.txt)

    def __repr__(self) -> bytes:
        return ec('Trans(string=%r, params=%r code=%r)' % (
            str(self),
            self.p,
            self.code,
        ))


trans = Trans
