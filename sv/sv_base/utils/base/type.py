
class NameValue:
    """
    为value添加名称属性
    """
    def __new__(cls, value, name=None):
        if isinstance(value, NameValue):
            return value

        obj = super().__new__(cls, value)
        obj.value = value
        obj.name = name

        return obj


class NameInt(NameValue, int):
    """
    为int value添加名称属性
    """
    def __new__(cls, value, name=None):
        if isinstance(value, NameInt):
            return value

        obj = super().__new__(NameInt, value)
        obj.value = value
        obj.name = name

        return obj


class NameStr(NameValue, str):
    """
    为str value添加名称属性
    """
    def __new__(cls, value, name=None):
        if isinstance(value, NameStr):
            return value

        obj = super().__new__(NameStr, value)
        obj.value = value
        obj.name = name

        return obj
