"""
django补丁

"""
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


def monkey_patch() -> None:
    """打补丁

    """
    migration_serializer.EnumSerializer = EnumSerializer
