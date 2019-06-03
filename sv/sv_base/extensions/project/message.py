import enum

from .trans import Trans


def generate_message_code(attr_name):
    """生成消息码。

    :param attr_name: 属性名称
    :return: 消息码
    """
    return attr_name


def message_call(self, *args, **kwargs):
    """枚举信息的call格式化参数调用

    :param self: 枚举对象
    :return: 格式化枚举信息实例
    """
    if isinstance(self.value, Trans):
        return self.value(*args, **kwargs)

    return self.value


def message_str(self, *args, **kwargs):
    """枚举信息的str调用

    :param self: 枚举对象
    :return: 枚举信息str
    """
    value = message_call(self, *args, **kwargs)
    return str(value)


class MessageMeta(enum.EnumMeta):
    def __new__(mcs, cls, bases, classdict):
        """初始化格式字典

        :param cls: 当前类名
        :param bases: 父类
        :param classdict: 类属性
        :return: 当前类
        """
        mcs._promise_messages(classdict)
        return enum.EnumMeta.__new__(mcs, cls, bases, classdict)

    @classmethod
    def _promise_messages(mcs, classdict):
        """修复类属性字典

        :param classdict: 类属性字典
        """
        messages = []
        for attr_name, message_desc in list(classdict.items()):
            if attr_name.isupper():
                message_code = generate_message_code(attr_name)
                if isinstance(message_desc, Trans):
                    message_desc.code = message_code
                    detail = message_desc
                elif isinstance(message_desc, str):
                    detail = Trans(message_desc, code=message_code)
                else:
                    message_desc.code = message_code
                    detail = message_desc

                messages.append((attr_name, detail))
                classdict._member_names.remove(attr_name)
                classdict._last_values.remove(message_desc)
                classdict.pop(attr_name)

        for attr_name, detail in messages:
            classdict[attr_name] = detail

        classdict['__call__'] = message_call
        classdict['__str__'] = message_str
        classdict['__json__'] = message_str
