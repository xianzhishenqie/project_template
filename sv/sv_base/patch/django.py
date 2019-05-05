"""
django补丁

"""
import builtins

from django.db import models
from django.db.migrations import serializer as migration_serializer


class EnumSerializer(migration_serializer.BaseSerializer):
    """
    migrations 解释枚举类型补丁
    """
    def serialize(self) -> tuple:
        enum_class = self.value.__class__
        module = enum_class.__module__
        v_string, v_imports = migration_serializer.serializer_factory(self.value.value).serialize()
        imports = {'import %s' % module, *v_imports}
        return "%s.%s(%s)" % (module, enum_class.__qualname__, v_string), imports


class TypeSerializer(migration_serializer.BaseSerializer):
    def serialize(self):
        special_cases = [
            (models.Model, "models.Model", []),
        ]
        for case, string, imports in special_cases:
            if case is self.value:
                return string, set(imports)
        if hasattr(self.value, "__module__"):
            module = self.value.__module__
            if module == builtins.__name__:
                return self.value.__name__, set()
            else:
                return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}


def monkey_patch() -> None:
    """打补丁

    """
    migration_serializer.EnumSerializer = EnumSerializer
    migration_serializer.TypeSerializer = TypeSerializer

    migration_serializer.Serializer.register(enum.Enum, EnumSerializer)
