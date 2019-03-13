from __future__ import annotations

import enum

from sv_base.utils.common.ubase import NameValue


class ChoiceMeta(enum.EnumMeta):

    @property
    def choices(self):
        items = []
        for key, value in self.__members__.items():
            val = value.value
            if isinstance(val, NameValue):
                items.append((val.value, val.name))
            else:
                items.append((val, key))

        return items


class Choice(enum.Enum, metaclass=ChoiceMeta):
    pass
