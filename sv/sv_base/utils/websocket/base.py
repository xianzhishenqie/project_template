from channels.generic.websocket import JsonWebsocketConsumer


class Websocket(JsonWebsocketConsumer):
    """
    websocket类, 添加自动组管理
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.groups is None:
            self.groups = self.get_group_names()

    def get_groups(self):
        return []

    def get_group_names(self):
        return [self.get_group_name(group) for group in self.get_groups()]

    @classmethod
    def group_prefix(cls):
        return '%s-%s' % (cls.__module__, cls.__name__)

    @classmethod
    def get_group_name(cls, name):
        return '%s.%s' % (cls.group_prefix(), name)
