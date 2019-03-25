import pickle
import sched
import threading
import time
from typing import Callable, Optional

from django.core.cache import cache
from sv_base.utils.common.utext import md5


def async_exe(func: Callable, args: tuple = None, kwargs: dict = None, delay: int = 0) -> threading.Thread:
    """异步执行方法

    :param func: 待执行方法
    :param args: 方法args参数
    :param kwargs: 方法kwargs参数
    :param delay: 执行延迟时间
    :return: 执行线程对象
    """
    args = args or ()
    kwargs = kwargs or {}

    def tmp():
        func(*args, **kwargs)
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(delay, 10, tmp, ())
    thread = threading.Thread(target=scheduler.run)
    thread.start()

    return thread


def async_exe_once(func: Callable,
                   args: tuple = None,
                   kwargs: dict = None,
                   delay: int = 0,
                   timeout: int = 3) -> Optional[threading.Thread]:
    """异步执行一次方法

    :param func: 待执行方法
    :param args: 方法args参数
    :param kwargs: 方法kwargs参数
    :param delay: 执行延迟时间
    :param timeout: 锁过期时间
    :return: 执行线程对象
    """
    exe_key = _exe_key(func, args, kwargs)
    # 利用缓存锁，是同一时间只能执行一次该方法
    result = cache.add(exe_key, 1, timeout)
    if not result:
        return

    return async_exe(func, args, kwargs, delay)


def _exe_key(func: Callable, args: tuple, kwargs: dict) -> str:
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
