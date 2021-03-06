import functools


def combine_validators(validators):
    """组合验证方法

    :param validators: 验证方法列表
    :return: 验证方法
    """

    def validate(self, attrs):
        for validator in validators:
            attrs = validator(self, attrs)
        return attrs

    return validate


class ValidatorBase(type):
    """
    验证配置元类，添加配置选项
    """

    field_validate_func_prefix = 'validate_'

    normal_validate_func_name = 'validate'

    def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(mcs, name, bases, attrs)
        # 解析资源配置选项
        meta = getattr(new_class, 'Meta', None)
        if meta is None:
            raise Exception('Cannot find meta config')

        has_model = hasattr(meta, 'model') and meta.model
        has_serializer_classes = hasattr(meta, 'serializer_classes') and meta.serializer_classes
        if has_model:
            name_field_map = {field.name: field for field in meta.model._meta.fields}
        else:
            name_field_map = {}

        for key, value in attrs.items():
            if key.startswith(mcs.field_validate_func_prefix):
                field_name = key[len(mcs.field_validate_func_prefix):]
                if field_name in name_field_map:
                    field = name_field_map[field_name]
                    if hasattr(value, 'validators') and value.validators:
                        field.validators.extend(value.validators)

                    if isinstance(value, list):
                        field.validators.extend(value)
                    else:
                        field.validators.append(value)
            elif key == mcs.normal_validate_func_name:
                if has_serializer_classes:
                    for serializer_class in meta.serializer_classes:
                        validate = combine_validators([value, serializer_class.validate])
                        setattr(serializer_class, 'validate', validate)

        return new_class


class Validator(metaclass=ValidatorBase):
    """验证配置基础类
    example:
        from django.core.validators import ValidationError


        def test_validate(value):
            if not value:
                raise ValidationError('test validate')


        class User(Validator):

            validate_username = [test_validate]

            @attach_validators([test_validate])
            def validate_name(value):
                if not value:
                    raise ValidationError('validate name')

            def validate(serializer, attrs):
                if not attrs.get('name'):
                    raise ValidationError('validate')

                return attrs

            class Meta:
                model = models.User
                serializer_classes = [UserSerializer]
    """
    class Meta:
        model = None
        serializer_classes = []


def attach_validators(validators):
    def wrapper(func):
        func.validators = validators
        @functools.wraps(func)
        def _wrapper(value):
            return func(value)
        return _wrapper
    return wrapper
