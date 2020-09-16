from rest_framework.fields import CharField


class RemoteFileField(CharField):

    def to_representation(self, value):
        if value:
            return value.url

        return super().to_representation(value)
