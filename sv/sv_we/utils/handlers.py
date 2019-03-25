
import time

from django.utils import timezone


class UserMessageHandler:

    def __init__(self, receive_data):
        msg_type = receive_data.get('MsgType')
        handle = getattr(self, 'handle_{}'.format(msg_type), None)
        if not handle:
            raise Exception('no message handler')

        self.handle = handle
        self.msg_type = msg_type
        self.from_username = receive_data.get('FromUserName')
        self.to_username = receive_data.get('ToUserName')
        self.create_time = receive_data.get('CreateTime')
        self.content = receive_data.get('Content')

    def result(self, data=None):
        res = {
            'ToUserName': self.from_username,
            'FromUserName': self.to_username,
            'CreateTime': int(time.mktime(timezone.now().timetuple())),
            'MsgType': self.msg_type,
            'Content': '',
        }
        if data:
            res.update(data)
        return res
