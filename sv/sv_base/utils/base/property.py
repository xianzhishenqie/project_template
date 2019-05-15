import functools
import types


def cached_property(func):
    """类的缓存属性装饰器

    :param func: 类的属性获取方法
    :return: 类的缓存属性
    """
    name = func.__name__
    _name = '_{}'.format(name)

    @functools.wraps(func)
    def fget(instance):
        if not hasattr(instance, _name):
            setattr(instance, _name, func(instance))
            add_cached_property(instance, name)

        value = getattr(instance, _name)
        return value

    def fset(instance, value):
        setattr(instance, _name, value)
        add_cached_property(instance, name)

    def fdel(instance):
        if hasattr(instance, _name):
            delattr(instance, _name)
            remove_cached_property(instance, name)

    return property(fget=fget, fset=fset, fdel=fdel)


instance_cached_properties_name = '_cached_properties'

instance_reset_cached_properties_name = 'reset_cached_properties'


def add_cached_property(instance, name):
    """添加缓存的属性

    :param instance: 实例对象
    :param name: 缓存的属性名称
    """
    if not hasattr(instance, instance_cached_properties_name):
        setattr(instance, instance_cached_properties_name, set())

    getattr(instance, instance_cached_properties_name).add(name)

    if not hasattr(instance, instance_reset_cached_properties_name):
        setattr(instance, instance_reset_cached_properties_name, types.MethodType(reset_cached_properties, instance))


def remove_cached_property(instance, name):
    """移除缓存的属性

    :param instance: 实例对象
    :param name: 缓存的属性名称
    """
    cached_properties = getattr(instance, instance_cached_properties_name, None)
    if cached_properties:
        cached_properties.remove(name)


def reset_cached_properties(instance):
    """移除所有缓存的属性

    :param instance: 实例对象
    """
    cached_properties = getattr(instance, instance_cached_properties_name, None)
    if cached_properties:
        for property_name in list(cached_properties):
            delattr(instance, property_name)
