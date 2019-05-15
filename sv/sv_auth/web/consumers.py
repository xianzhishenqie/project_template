from sv_base.extensions.websocket import Websocket
from sv_auth.models import User


class UserWebsocket(Websocket):
    """
    基于用户的websocket服务类
    """

    enable_auth = True

    @property
    def user(self):
        """连接用户

        :return: user
        """
        return self.scope['user']

    def get_groups(self):
        """获取用户组

        :return: 用户组
        """
        if self.enable_auth:
            groups = [self.user_group_name(self.user)]
        else:
            groups = []

        return groups

    @classmethod
    def user_group_name(cls, user):
        """格式化用户组名

        :param user: 用户/用户id
        :return: 用户组名
        """
        if isinstance(user, User):
            user_id = user.id
        else:
            user_id = user

        return f'user-{user_id}'

    @classmethod
    def user_send(cls, user, content):
        """向用户推送消息

        :param user: 用户/用户列表
        :param content: 消息内容
        """
        if isinstance(user, (list, tuple, set)):
            users = user
        else:
            users = [user]

        for usr in users:
            cls.group_send(cls.user_group_name(usr), content)

    def check_auth(self):
        """连接鉴权

        :return: bool
        """
        if self.enable_auth and not self.user.is_authenticated:
            self.close()
            return False
        return True

    def websocket_connect(self, message):
        """websocket连接时处理

        :param message: 消息体
        """
        if not self.check_auth():
            return

        super().websocket_connect(message)

    def websocket_receive(self, message):
        """websocket接收时处理

        :param message: 消息体
        """
        if not self.check_auth():
            return

        super().websocket_receive(message)

    def websocket_disconnect(self, message):
        """websocket断开时处理

        :param message: 消息体
        """
        if not self.check_auth():
            return

        super().websocket_disconnect(message)
