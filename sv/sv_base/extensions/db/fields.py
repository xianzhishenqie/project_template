import os

from django.db.models import CharField
from django.utils.translation import gettext_lazy as _

from sv_base.utils.base.property import cached_property
from sv_base.utils.tools.file import FileClient


class RemoteFieldFile(str):

    def __new__(cls, instance, field, value):
        if isinstance(value, RemoteFieldFile):
            return value

        obj = super().__new__(RemoteFieldFile, value)
        obj.instance = instance
        obj.field = field

        return obj

    def _require_file(self):
        if not self:
            raise ValueError("The '%s' attribute has no file associated with it." % self.field.name)

    @cached_property
    def storage(self):
        return FileClient()

    @cached_property
    def memory_file(self):
        self._require_file()
        return self.storage.download_as_memory_file(self)

    @cached_property
    def local_file(self):
        self._require_file()
        return self.storage.download_as_tmp_file(self)

    @property
    def url(self):
        self._require_file()
        return self.storage.url(self)

    def delete(self):
        if not self:
            return

        self.clear()
        self.storage.delete(self)

    def clear(self):
        if hasattr(self, '_memory_file'):
            self.memory_file.close()
            del self.memory_file

        if hasattr(self, '_local_file'):
            try:
                os.remove(self.local_file)
            except Exception:
                pass

            del self.local_file


class RemoteFileDescriptor:
    """
    远程文件描述符
    """
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        if self.field.name in instance.__dict__:
            file = instance.__dict__[self.field.name]
        else:
            instance.refresh_from_db(fields=[self.field.name])
            file = getattr(instance, self.field.name)

        if not file:
            attr = self.field.attr_class(instance, self.field, '')
            instance.__dict__[self.field.name] = attr
        elif isinstance(file, str) and not isinstance(file, RemoteFieldFile):
            file_copy = self.field.attr_class(instance, self.field, file)
            instance.__dict__[self.field.name] = file_copy
        elif isinstance(file, RemoteFieldFile) and not hasattr(file, 'field'):
            file.instance = instance
            file.field = self.field
        elif isinstance(file, RemoteFieldFile) and instance is not file.instance:
            file.instance = instance

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value


class RemoteFileField(CharField):
    description = _("RemoteFile")

    attr_class = RemoteFieldFile

    descriptor_class = RemoteFileDescriptor

    def __init__(self, verbose_name=None, *args, **kwargs):
        verbose_name = verbose_name or _('x_remote_file')
        kwargs.setdefault('max_length', 512)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('default', '')
        super().__init__(verbose_name, *args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, self.descriptor_class(self))
