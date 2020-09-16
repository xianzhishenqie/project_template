import time

from nameko.runners import ServiceRunner
from django.conf import settings

from sv_base.utils.base.func import get_func_key
from sv_base.utils.base.thread import async_exe
from sv_base.extensions.service.base import ServiceBase, send_event, event_handler, get_config
from sv_base.extensions.service.rpc import get_context as get_rpc_context

MESSAGE_CONTEXT_KEY = '_'

get_context = get_rpc_context


def get_context_key():
    context = get_context()
    return context.get(MESSAGE_CONTEXT_KEY)


def send_message(key, data, timeout=None, **kwargs):
    """
    发送消息
    :param key: 消息识别key
    :param data: 消息数据
    :param timeout: 消息过期时间
    """
    send_event(key, data, timeout=timeout, **kwargs)


class MergeMessageSender:
    """
    发送可合并的发送行为（不重要的数据），延时发送最新一条消息, 减少消息压力，但会降低实时性
    """
    def __init__(self, key, timeout=5, check_time=3):
        # 必须指定消息路由，只合并同种消息
        self.key = key
        # 准备发送的检测时间
        self.check_time = check_time
        # 当前是否处于准备发送的检测状态
        self.checking = False

        self.data = None
        self.timeout = timeout

    def send(self, data):
        # 更新发送的消息为最新
        self.data = data

        if self.checking:
            return

        async_exe(self._send)

    def _send(self):
        self.checking = True
        time.sleep(self.check_time)
        self.checking = False
        send_message(self.key, self.data, timeout=self.timeout)


def get_message_listener(key, callback, context_key=None, **kwargs):
    """
    获取消息监听器
    :param key: 消息识别key
    :param callback: 回调函数
    :param context_key: 消息上下文识别key
    :return: 消息监听器
    """
    class MessageReceiver(ServiceBase):
        name = f'message_receiver_{key}_{get_func_key(callback)}'

        @event_handler(key, **kwargs)
        def receive(self, data):
            if context_key:
                current_context_key = get_context_key()
                if (context_key == current_context_key
                        or (isinstance(current_context_key, (list, tuple)) and context_key in current_context_key)):
                    callback(data)
            else:
                callback(data)

    return MessageReceiver


def message_listener(key, context_key=None):
    """
    消息回调函数装饰器，添加消息识别key
    :param key: 消息识别key
    :param context_key: 消息上下文识别key
    :return: 消息回调函数装饰器
    """
    def _callback(callback):
        callback._message_listener_key = key
        callback._message_listener_context_key = context_key
        return callback
    return _callback


def listen_message(key, callback, context_key=None, timeout=None, block=False, pool_name=None, **kwargs):
    """
    监听消息
    :param key: 消息识别key
    :param callback: 回调函数
    :param context_key: 消息上下文识别key
    :param timeout: 超时关闭监听
    :param block: 是否阻塞
    :param pool_name: 配置池名称
    :return: 无
    """
    message_listener = get_message_listener(key, callback, context_key, **kwargs)
    config = get_config(settings.NAMEKO_CONFIG, name=pool_name)
    service_runner = ServiceRunner(config)
    service_runner.add_service(message_listener)
    service_runner.start()
    if timeout:
        def stop():
            time.sleep(timeout)
            service_runner.stop()

        if block:
            stop()
        else:
            async_exe(stop)

    return service_runner
