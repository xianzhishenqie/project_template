from django.middleware import csrf
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def csrf_token(request):
    """获取csrf_token

    :param request: 请求对象
    :return: 请求响应对象
    """
    token = csrf.get_token(request)
    return Response({'token': token})
