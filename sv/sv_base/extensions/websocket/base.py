from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer
from channels.generic.websocket import JsonWebsocketConsumer

from sv_base.utils.base.task import SyncTaskPool


class Websocket(JsonWebsocketConsumer):
    """
    websocket类, 添加自动组管理
    """

    sync_task_pool = SyncTaskPool()

    def get_groups(self):
        """获取组列表, 子类重写

        :return: 组列表
        """
        return []

    def get_group_names(self):
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
    def get_group_name(cls, name):
        """生成组名称

        :param name: 组相对名称
        :return: 组绝对名称
        """
        return '%s.%s' % (cls.group_prefix(), name)

    @classmethod
    def get_channel_layer(cls):
        """获取channel_layer

        :return: channel_layer
        """
        return get_channel_layer(cls.channel_layer_alias)

    def group_message(self, message):
        """组消息处理

        :param message: 消息内容
        """
        self.send_json(message["content"], close=message["close"])

    @classmethod
    def group_send(cls, group, content, close=False):
        """组发送消息

        :param group: 组名
        :param content: 消息内容
        :param close: 是否关闭连接
        """
        channel_layer = cls.get_channel_layer()
        group_send = async_to_sync(channel_layer.group_send)
        group_name = cls.get_group_name(group)
        group_send(group_name, {
            'type': 'group.message',
            'content': content,
            'close': close,
        })

    @classmethod
    def group_send_task(cls, group, content, close=False):
        cls.sync_task_pool.add(cls.group_send, kwargs={
            'group': group,
            'content': content,
            'close': close,
        })

    def websocket_connect(self, message):
        self.groups = self.get_group_names()
        super().websocket_connect(message)
