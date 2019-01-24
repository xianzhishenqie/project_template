from django.utils.encoding import force_text

from rest_framework import exceptions
from rest_framework.fields import FileField
from rest_framework.settings import api_settings
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

from sv_base.utils.common.utext import Trans


def _get_error_details(data, default_code=None):
    """
    Descend into a nested data structure, forcing any
    lazy translation strings or strings into `ErrorDetail`.
    """
    if isinstance(data, list):
        ret = [
            _get_error_details(item, default_code) for item in data
        ]
        if isinstance(data, ReturnList):
            return ReturnList(ret, serializer=data.serializer)
        return ret
    elif isinstance(data, dict):
        ret = {
            key: _get_error_details(value, default_code)
            for key, value in data.items()
        }
        if isinstance(data, ReturnDict):
            return ReturnDict(ret, serializer=data.serializer)
        return ret
    elif isinstance(data, Trans):
        return data

    text = force_text(data)
    code = getattr(data, 'code', default_code)
    return exceptions.ErrorDetail(text, code)


def _get_full_details(detail):
    if isinstance(detail, list):
        return [_get_full_details(item) for item in detail]
    elif isinstance(detail, dict):
        return {key: _get_full_details(value) for key, value in detail.items()}
    return {
        'message': detail,
        'params': getattr(detail, 'p', None),
        'code': detail.code
    }


def file_field_to_representation(self, value):
    if not value:
        return None

    use_url = getattr(self, 'use_url', api_settings.UPLOADED_FILES_USE_URL)

    if use_url:
        if not getattr(value, 'url', None):
            # If the file has not been saved it may not have a URL.
            return None
        return value.url
    return value.name


def monkey_patch():
    exceptions._get_error_details = _get_error_details
    exceptions._get_full_details = _get_full_details
    FileField.to_representation = file_field_to_representation
