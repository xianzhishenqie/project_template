import pickle
import sched
import threading
import time

from django.core.cache import cache
from sv_base.utils.base.text import md5


def async_exe(func, args=None, kwargs=None, delay=0, shared_config=None):
    """异步执行方法

    :param func: 待执行方法
    :param args: 方法args参数
    :param kwargs: 方法kwargs参数
    :param delay: 执行延迟时间
    :param shared_config: 共享配置{'get_shared': 获取共享线程变量参数, 'set_shared': 设置共享线程变量}
    :return: 执行线程对象
    """
    args = args or ()
    kwargs = kwargs or {}

    shared_config = shared_config or {
        'get_shared': get_shared,
        'set_shared': set_shared,
    }
    enable_shared = shared_config.get('enable_shared', True)
    if enable_shared:
        shared = shared_config['get_shared']()

    def tmp():
        if enable_shared:
            shared_config['set_shared'](shared)

        func(*args, **kwargs)
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(delay, 10, tmp, ())
    thread = threading.Thread(target=scheduler.run)
    thread.start()

    return thread


def async_exe_once(func, args=None, kwargs=None, delay=0, timeout=3, shared_config=None):
    """异步执行一次方法

    :param func: 待执行方法
    :param args: 方法args参数
    :param kwargs: 方法kwargs参数
    :param delay: 执行延迟时间
    :param timeout: 锁过期时间
    :param shared_config: 共享配置{'get_shared': 获取共享线程变量参数, 'set_shared': 设置共享线程变量}
    :return: 执行线程对象
    """
    exe_key = _exe_key(func, args, kwargs)
    # 利用缓存锁，是同一时间只能执行一次该方法
    result = cache.add(exe_key, 1, timeout)
    if not result:
        return

    return async_exe(func, args, kwargs, delay, shared_config)


def _exe_key(func, args, kwargs):
    """方法识别key

    :param func: 待执行方法
    :param args: 方法args参数
    :param kwargs: 方法kwargs参数
    :return: 方法识别key
    """
    exe_key = md5('{func}(*{args}, **{kwargs})'.format(
        func=pickle.dumps(func),
        args=pickle.dumps(args),
        kwargs=pickle.dumps(kwargs),
    ))

    return exe_key


class Shared:
    key = 'shared_key'

    @classmethod
    def _get_shared(cls):
        raise NotImplementedError()

    @classmethod
    def _set_shared(cls, data):
        raise NotImplementedError()

    @classmethod
    def get_shared(cls):
        return {
            cls.key: cls._get_shared(),
        }

    @classmethod
    def set_shared(cls, shared_data):
        data = shared_data[cls.key]
        return cls._set_shared(data)


shared_classes = set()


def get_shared():
    """
    获取共享线程变量参数
    :return: 共享线程变量参数
    """
    shared_data = {}
    for shared_class in shared_classes:
        shared_data.update(shared_class.get_shared())

    return shared_data


def set_shared(shared_data):
    """
    设置共享线程变量
    :param shared_data: 共享线程变量
    :return: 无
    """
    for shared_class in shared_classes:
        shared_class.set_shared(shared_data)


def register_shared(classes):
    shared_classes.update(classes)
