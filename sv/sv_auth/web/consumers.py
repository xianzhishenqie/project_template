from channels.layers import get_channel_layer

from sv_base.utils.websocket import Websocket

from sv_auth.models import User


channel_layer = get_channel_layer()


class UserWebsocket(Websocket):

    enable_auth = False

    @property
    def user(self):
        return self.scope['user']

    def get_groups(self):
        return [self.user_group_name(self.user)]

    @classmethod
    def user_group_name(cls, user):
        if isinstance(user, User):
            user_id = user.id
        else:
            user_id = user

        return 'user-{user_id}'.format(user_id=user_id)

    @classmethod
    def user_send(cls, user, content):
        if isinstance(user, (list, tuple, set)):
            users = user
        else:
            users = [user]

        for usr in users:
            channel_layer.group_send(cls.user_group_name(usr), content)

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
