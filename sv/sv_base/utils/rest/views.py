from rest_framework import exceptions
from rest_framework.views import exception_handler as base_exception_handler


def exception_handler(exc, context):
    response = base_exception_handler(exc, context)
    if isinstance(exc, exceptions.APIException):
        if isinstance(exc.detail, (list, dict)):
            data = exc.get_full_details()
        else:
            data = {'__global': exc.get_full_details()}
        response.data = data

    return response