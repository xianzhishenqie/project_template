from __future__ import annotations

from typing import Optional


class NameValue:
    """
    为value添加名称属性
    """
    def __new__(cls, value: object, name: Optional[str] = None) -> NameValue:
        obj = super(NameValue, cls).__new__(cls, value)
        obj.value = value
        obj.name = name
        return obj


class NameInt(NameValue, int):
    """
    为int value添加名称属性
    """
    pass


class NameStr(NameValue, str):
    """
    为str value添加名称属性
    """
    pass
