import json

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as base_exception_handler


def exception_handler(exc, context):
    """rest api异常处理

    :param exc: 异常
    :param context: 上下文
    :return: 请求响应
    """
    if hasattr(exc, "exc_type"):
        exec_type = getattr(exc, 'exc_type', None)
        if exec_type == "RestException":
            return Response(json.loads(exc.value), status=status.HTTP_400_BAD_REQUEST)

    response = base_exception_handler(exc, context)
    if isinstance(exc, exceptions.APIException):
        if isinstance(exc.detail, (list, dict)):
            data = exc.get_full_details()
        else:
            data = {'__global': exc.get_full_details()}
        response.data = data

    return response
