import functools
import inspect
import json
import logging
import types

from django.core.cache import _create_cache
from django.conf import settings

from sv_base.utils.base.text import md5

logger = logging.getLogger(__name__)


class CacheProduct:
    """
    memcached引擎缓存类
    """

    def __new__(cls, name):
        # 创建一个新的缓存实例
        cache_instance = _create_cache('default')

        # 根据缓存实例名称生成该缓存的版本号键
        version = cls.get_version(name)
        cache_instance.version = version
        setattr(cache_instance, 'reset', types.MethodType(delete_cache, cache_instance))
        return cache_instance

    # 生成版本号
    @classmethod
    def get_version(cls, name):
        return md5('%s:cache' % name)


def delete_cache(cache_instance):
    """删除该缓存

    :param cache_instance: 缓存实例
    """
    try:
        return cache_instance.delete_pattern('*')
    except Exception as e:
        logger.error('delete cache error: %s', e)


def default_key_func(method, *args, **kwargs):
    arg_dict = inspect.getcallargs(method, *args, **kwargs)
    arg_dict.update({
        '__qualname__': method.__qualname__,
        '__module__': method.__module__,
    })

    arg_dict.pop('self', None)
    arg_dict.pop('cls', None)

    return md5(json.dumps(arg_dict, sort_keys=True).encode('utf-8'))


def func_cache(cache=None, key_func=None, key_prefix=None, expires=settings.DEFAULT_CACHE_AGE):
    """
    方法的cache
    :param cache: 缓存操作实例
    :param key_func: 生成cache_key的方法
    :param key_prefix: 缓存的key前缀
    :param expires: 缓存过期时间，单位秒
    :return:
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = ''
            if callable(key_func):
                key = key_func(func, *args, **kwargs)
            else:
                key = default_key_func(func, *args, **kwargs)

            if not key:
                return func(*args, **kwargs)

            if key_prefix is not None:
                key = f'{key_prefix(func, *args, **kwargs)}:{key}' if callable(key_prefix) else f'{key_prefix}:{key}'

            if isinstance(cache, str):
                cache_instance = CacheProduct(cache)
            else:
                cache_instance = cache or CacheProduct('default_func_cache')

            cache_data = cache_instance.get(key)
            if cache_data is not None:
                return cache_data

            result = func(*args, **kwargs)

            cache_instance.set(key, result, expires)

            return result

        return wrapper

    return decorator
