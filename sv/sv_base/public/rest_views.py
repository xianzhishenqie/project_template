
from django.middleware import csrf
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def csrf_token(request):
    token = csrf.get_token(request)
    return Response({'token': token})
