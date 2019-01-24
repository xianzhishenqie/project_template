
import functools

from sv_base.utils.rest.request import RequestData


def api_request_data(strict=False):
    def wrapper(func):
        @functools.wraps(func)
        def _wrapper(view, request, *args, **kwargs):
            view.query_data = request.query_data = RequestData(request, is_query=True, strict=strict)
            view.shift_data = request.shift_data = RequestData(request, is_query=False, strict=strict)
            return func(view, request, *args, **kwargs)
        return _wrapper
    return wrapper


def request_data(strict=False):
    def wrapper(func):
        @functools.wraps(func)
        def _wrapper(request, *args, **kwargs):
            request.query_data = RequestData(request, is_query=True, strict=strict)
            request.shift_data = RequestData(request, is_query=False, strict=strict)
            return func(request, *args, **kwargs)
        return _wrapper
    return wrapper

