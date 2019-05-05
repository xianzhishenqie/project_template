from django import forms
from django.db import models
from django.core.exceptions import ValidationError

from sv_base.extensions.project.trans import Trans as _
from sv_base.utils.base.list import value_filter


class InvalidStatusOperationError(ValidationError):
    pass


class EnumField(models.Field):
    """ 自定义的枚举Field
    """

    def __init__(self, enum, *args, **kwargs):
        """初始化枚举选项和默认值

        :param enum: 枚举选项
        """
        kwargs['choices'] = enum.choices()
        if 'default' not in kwargs:
            kwargs['default'] = enum.default()
        self.enum = enum
        super(EnumField, self).__init__(*args, **kwargs)

    def contribute_to_class(
        self, cls, name, private_only=False, virtual_only=models.NOT_PROVIDED
    ):
        super(EnumField, self).contribute_to_class(cls, name)
        models.signals.class_prepared.connect(self._setup_validation, sender=cls)

    def _setup_validation(self, sender, **kwargs):
        """添加字段设置验证

        :param sender: 数据对象
        """
        att_name = self.get_attname()
        enum = self.enum

        def field_set(self, new_value):
            # Run validation for new value.
            valid_value = validate_available_choice(enum, new_value)
            # Update private enum attribute with new value
            self.__dict__[att_name] = valid_value

        def field_get(self):
            return self.__dict__[att_name]

        if not sender._meta.abstract:
            setattr(sender, att_name, property(fget=field_get, fset=field_set))

    def validate(self, value, model_instance):
        super(EnumField, self).validate(value, model_instance)
        validate_available_choice(self.enum, value)

    def formfield(self, **kwargs):
        defaults = {'widget': forms.Select,
                    'form_class': forms.TypedChoiceField,
                    'coerce': int,
                    'choices': self.enum.choices(blank=self.blank)}
        defaults.update(kwargs)
        return super(EnumField, self).formfield(**defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(EnumField, self).deconstruct()
        kwargs['enum'] = self.enum
        if 'choices' in kwargs:
            del kwargs['choices']
        return name, path, args, kwargs


def validate_available_choice(enum, to_value):
    """验证字段值是否有效

    :param enum: 字段枚举选项
    :param to_value: 字段值
    :return: 有效的字段值
    """
    if to_value is None:
        return

    valid_values = [choice[0] for choice in enum.choices()]
    valid_value = value_filter(to_value, valid_values)
    if valid_value is None:
        message = _('x_invalid_field_choice')(value=to_value)
        raise InvalidStatusOperationError(message)

    return valid_value


class IntegerEnumField(EnumField, models.IntegerField):
    pass


class CharEnumField(EnumField, models.CharField):
    pass
