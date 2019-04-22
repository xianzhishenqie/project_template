import types

from django.core.cache import _create_cache

from sv_base.utils.base.text import md5


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


def delete_cache(cache_instance: object) -> int:
    """删除该缓存

    :param cache_instance: 缓存实例
    """
    return cache_instance.delete_pattern('*')
