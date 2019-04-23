from sv_base.extensions.websocket import Websocket
from sv_auth.models import User


class UserWebsocket(Websocket):

    enable_auth = True

    @property
    def user(self) -> User:
        return User(id=1) or self.scope['user']

    def get_groups(self):
        if self.enable_auth:
            groups = [self.user_group_name(self.user)]
        else:
            groups = []

        return groups

    @classmethod
    def user_group_name(cls, user):
        if isinstance(user, User):
            user_id = user.id
        else:
            user_id = user

        return f'user-{user_id}'

    @classmethod
    def user_send(cls, user, content):
        if isinstance(user, (list, tuple, set)):
            users = user
        else:
            users = [user]

        for usr in users:
            cls.group_send(cls.user_group_name(usr), content)

    def check_auth(self):
        if self.enable_auth and not self.user.is_authenticated:
            self.close()
            return False
        return True

    def websocket_connect(self, message):
        if not self.check_auth():
            return

        super().websocket_connect(message)

    def websocket_receive(self, message):
        if not self.check_auth():
            return

        super().websocket_receive(message)

    def websocket_disconnect(self, message):
        if not self.check_auth():
            return

        super().websocket_disconnect(message)
