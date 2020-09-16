import enum

from sv_base.utils.base.type import NameValue, NameInt, NameStr
from sv_base.extensions.db.fields import RemoteFileField


STATUS_DELETED = 0


class Choice(enum.Enum):
    """
    Model选项枚举类
    """
    @classmethod
    def choices(cls, blank=False):
        items = []
        for key, value in cls.__members__.items():
            val = value.value
            if isinstance(value, NameValue):
                items.append((value.value, value.name))
            else:
                items.append((val, key))

        if blank:
            sampl_val = items[0][0]
            if isinstance(sampl_val, int):
                items.insert(0, (0, ''))
            else:
                items.insert(0, ('', ''))

        return items

    @classmethod
    def default(cls):
        return cls.choices()[0][0]


class IntChoice(NameInt, Choice):
    pass


class StrChoice(NameStr, Choice):
    pass


__all__ = [
    'STATUS_DELETED',
    'Choice',
    'IntChoice',
    'StrChoice',
    'RemoteFileField',
]
