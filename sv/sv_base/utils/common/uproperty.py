import functools
import types


def cached_property(func):
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


def add_cached_property(instance, name):
    if not hasattr(instance, '_cached_propertys'):
        instance._cached_propertys = set()

    instance._cached_propertys.add(name)

    if not hasattr(instance, 'reset_cached_propertys'):
        instance.reset_cached_propertys = types.MethodType(reset_cached_propertys, instance)


def remove_cached_property(instance, name):
    if hasattr(instance, '_cached_propertys'):
        instance._cached_propertys.remove(name)


def reset_cached_propertys(instance):
    if hasattr(instance, '_cached_propertys'):
        for property_name in list(instance._cached_propertys):
            delattr(instance, property_name)
