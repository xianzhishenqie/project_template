import functools

from django.core.cache import cache

from sv_base.utils.base.text import md5


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


def get_func_key(func):
    """
    获取函数识别键，顶层函数模块名区分，内部函数id区分
    :param func: 函数
    :return: 函数识别键
    """
    func_name = func.__qualname__
    complete_func_name = f'{func.__module__}.{func_name}'
    if '<locals>' in func_name.split('.'):
        complete_func_name = f'{complete_func_name}-{id(func)}'

    return md5(complete_func_name)
