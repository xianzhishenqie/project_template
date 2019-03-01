import uuid

from django.core.cache import cache, _create_cache

from sv_base.utils.common.utext import md5


class CacheProduct:
    """
    memcached引擎缓存类
    """
    def __new__(cls, name):
        # 创建一个新的缓存实例
        cache_instance = _create_cache('default')

        # 根据缓存实例名称生成该缓存的版本号键
        version_key = cls.get_version_key(name)
        cache_instance.version_key = version_key

        # 根据版本号键查询对应缓存版本
        version = cache.get(version_key)
        if version is None:
            # 查不到则生成一个唯一版本号, 并不过期的保存版本号(memcached最长30天，redis?)
            version = cls.get_unique_version()
            cache.set(version_key, version, None)
        cache_instance.version = version
        return cache_instance

    # 生成唯一版本号
    @classmethod
    def get_unique_version(cls):
        return str(uuid.uuid4())

    # 每个缓存对应的版本号键, 用以查询缓存当前版本号
    @classmethod
    def get_version_key(cls, name):
        return md5('%s:version' % name)


def delete_cache(cache_instance):
    # 更新缓存版本等于删除该缓存
    new_version = CacheProduct.get_unique_version()
    cache.set(cache_instance.version_key, new_version, None)
    cache_instance.version = new_version
