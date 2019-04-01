from __future__ import annotations

from typing import Union

from django.utils.encoding import force_text

from sv_base.utils.base.text import ec


class Trans(str):
    """
    国际化字符串类
    """
    # 收集所有的国际化字符串
    source = set()

    code = None

    # 格式化参数
    p = None

    def __new__(cls, s: str, code: Union[int, str, None] = None) -> Trans:
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
