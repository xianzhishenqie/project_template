from channels.generic.websocket import JsonWebsocketConsumer


class Websocket(JsonWebsocketConsumer):
    """
    websocket类, 添加自动组管理
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.groups is None:
            self.groups = self.get_group_names()

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
        return '%s-%s' % (cls.__module__, cls.__name__)

    @classmethod
    def get_group_name(cls, name: str) -> str:
        """生成组名称

        :param name: 组相对名称
        :return: 组绝对名称
        """
        return '%s.%s' % (cls.group_prefix(), name)
