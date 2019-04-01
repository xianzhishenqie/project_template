from django.conf import settings
from django.http.request import HttpRequest


def get_language_code(request: HttpRequest) -> str:
    """获取请求的国际化语言

    :param request: 请求对象
    :return: 语言
    """
    return getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)


def get_ip(request: HttpRequest) -> str:
    """获取请求的ip地址

    :param request: 请求对象
    :return: ip地址
    """
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        return request.META['HTTP_X_FORWARDED_FOR']
    elif 'REMOTE_ADDR' in request.META:
        return request.META['REMOTE_ADDR']
    else:
        return ''
