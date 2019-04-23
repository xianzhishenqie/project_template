from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer
from channels.generic.websocket import JsonWebsocketConsumer


class Websocket(JsonWebsocketConsumer):
    """
    websocket类, 添加自动组管理
    """
    def __init__(self, *args, **kwargs):
        if self.groups is None:
            self.groups = self.get_group_names()

        super().__init__(*args, **kwargs)

    def get_groups(self) -> list:
        """获取组列表, 子类重写

        :return: 组列表
        """
        return []

    def get_group_names(self) -> list:
        """自动获取组名称列表

        :return: 组名称列表
        """
        return [self.get_group_name(group) for group in self.get_groups()]

    @classmethod
    def group_prefix(cls):
        """生成组名称前缀

        :return: 组名称前缀
        """
        return '%s.%s' % (cls.__module__, cls.__name__)

    @classmethod
    def get_group_name(cls, name: str) -> str:
        """生成组名称

        :param name: 组相对名称
        :return: 组绝对名称
        """
        return '%s.%s' % (cls.group_prefix(), name)

    @classmethod
    def get_channel_layer(cls):
        return get_channel_layer(cls.channel_layer_alias)

    def group_message(self, message):
        self.send_json(message["content"], close=message["close"])

    @classmethod
    def group_send(cls, group, content, close=False):
        channel_layer = cls.get_channel_layer()
        group_send = async_to_sync(channel_layer.group_send)
        group_name = cls.get_group_name(group)
        group_send(group_name, {
            'type': 'group.message',
            'content': content,
            'close': close,
        })
