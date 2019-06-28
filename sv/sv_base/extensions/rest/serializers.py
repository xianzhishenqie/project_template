from rest_framework import serializers
from .request import set_dict_data


class ModelSerializer(serializers.ModelSerializer):
    """
    序列化类，可根据传入fields自动序列化对应字段

    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(ModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def _get_request(self):
        return self.context.get('request')

    def _get_user(self):
        user = self.context.get('user')
        if not user:
            request = self._get_request()
            user = request.user if request else None
            if user:
                self.context['user'] = user

        return user

    def _get_latest_attr(self, attr_name, validated_data, instance=None):
        if attr_name in validated_data:
            return validated_data[attr_name]
        else:
            if instance:
                return getattr(instance, attr_name)

        raise AttributeError(f'no attribute: {attr_name}')

    def _is_attr_changed(self, attr_name, validated_data, instance=None):
        if attr_name in validated_data:
            attr_value = validated_data[attr_name]
            if instance:
                return attr_value == getattr(instance, attr_name)
            else:
                return False
        else:
            return False

    def _set_data(self, data, name, value=None, remove=False):
        return set_dict_data(data, name, value=value, remove=remove)
