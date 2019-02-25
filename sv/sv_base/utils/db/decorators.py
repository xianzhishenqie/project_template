
import functools

from .common import close_old_connections


def promise_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        close_old_connections()
        return func(*args, **kwargs)
    return wrapper
