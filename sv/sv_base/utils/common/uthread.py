import pickle
import sched
import threading
import time

from django.core.cache import cache
from sv_base.utils.common.utext import md5


def async_exe(func, args=None, kwargs=None, delay=0):
    args = args or ()
    kwargs = kwargs or {}
    def tmp():
        func(*args, **kwargs)
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(delay, 10, tmp, ())
    thread = threading.Thread(target=scheduler.run)
    thread.start()

    return thread


def async_exe_once(func, args=None, kwargs=None, delay=0, timeout=3):
    exe_key = _exe_key(func, args, kwargs)
    result = cache.add(exe_key, 1, timeout)
    if not result:
        return

    return async_exe(func, args, kwargs, delay)


def _exe_key(func, args, kwargs):
    exe_key = md5('{func}(*{args}, **{kwargs})'.format(
        func=pickle.dumps(func),
        args=pickle.dumps(args),
        kwargs=pickle.dumps(kwargs),
    ))

    return exe_key
