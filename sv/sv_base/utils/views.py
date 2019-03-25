
from django.views import defaults


class Http404Page:
    """
    默认的404页面响应
    """
    def __new__(cls, request, exception=None):
        exception = exception or Exception()
        return defaults.page_not_found(request, exception)


class Http403Page:
    """
    默认的403页面响应
    """
    def __new__(cls, request, exception=None):
        exception = exception or Exception()
        return defaults.permission_denied(request, exception)


class Http400Page:
    """
    默认的400页面响应
    """
    def __new__(cls, request, exception=None):
        exception = exception or Exception()
        return defaults.bad_request(request, exception)


class Http500Page:
    """
    默认的500页面响应
    """
    def __new__(cls, request):
        return defaults.server_error(request)
