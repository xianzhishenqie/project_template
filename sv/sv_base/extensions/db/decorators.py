import functools

from .common import close_old_connections


def promise_db_connection(func):
    """确保有效的数据库连接装饰器

    :param func: 涉及数据库操作的执行方法
    :return: 执行方法
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        close_old_connections()
        return func(*args, **kwargs)
    return wrapper
