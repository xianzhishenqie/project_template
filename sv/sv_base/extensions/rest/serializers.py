from rest_framework import serializers


class ModelSerializer(serializers.ModelSerializer):
    """
    序列化类，可根据传入fields自动序列化对应字段

    """

    def __init__(self, *args, **kwargs) -> None:
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
