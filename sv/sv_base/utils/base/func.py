import functools

from django.core.cache import cache


def sync_func(key_func, timeout=1, exit_func=None):
    """
    同步装饰器

    :param key_func: 键生成函数
    :param timeout: 锁超时时间
    :param exit_func: 退出函数
    :return: 同步方法
    """
    def wrapper(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            key = key_func(func, *args, **kwargs)
            result = cache.add(key, 1, timeout)
            if not result:
                return exit_func(*args, **kwargs) if exit_func else None

            return func(*args, **kwargs)

        return _wrapper

    return wrapper
