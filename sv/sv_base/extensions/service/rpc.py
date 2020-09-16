import json
import logging
from threading import local
import zlib
import functools
from django.utils import translation
from nameko.constants import LANGUAGE_CONTEXT_KEY
from nameko.events import event_handler as base_event_handler
from nameko.rpc import rpc as base_rpc
from rest_framework import exceptions

from sv_base.utils.base.text import dc, ec
from sv_base.extensions.db.decorators import promise_db_connection

logger = logging.getLogger(__name__)


COMPRESS_CONTEXT_KEY = 'compress'


class APIException(Exception):
    """
    rpc api异常类
    """
    pass


class RestException(APIException):
    """
    rpc api rest异常类
    """
    pass


class RpcResult:
    """
    rpc 自定义处理返回值
    """
    def __init__(self, result, rely_callback=None):
        self.result = result
        self.rely_callback = rely_callback


_context = local()


def set_context(context):
    """
    设置rpc调用线程上下文
    :param context: 上下文
    :return: 无
    """
    language = context.get(LANGUAGE_CONTEXT_KEY)
    if language:
        translation.activate(language)

    _context.value = context


def get_context():
    """
    获取rpc线程上下文
    :return: rpc线程上下文
    """
    if not hasattr(_context, 'value'):
        _context.value = {}

    return _context.value


def rpc_log(func, self, *args, **kwargs):
    context = get_context()
    msg = f'[RPC CALLED] {self.name}:{func.__name__}, args: {args}, kwargs: {kwargs}, context: {context},'
    logger.debug(msg)


def compress_params(args, kwargs):
    """
    压缩参数
    """
    param_str = json.dumps({
        'args': args,
        'kwargs': kwargs,
    })
    param_str = zlib.compress(ec(param_str))

    return (param_str,), {}


def decompress_params(args, kwargs):
    """
    解压缩参数
    """
    param_str = args[0]
    param_str = dc(zlib.decompress(param_str))
    param = json.loads(param_str)

    return param['args'], param['kwargs']


def rpc(func):
    """
    添加自定义处理
    """
    @base_rpc
    @promise_db_connection
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.context.pop(COMPRESS_CONTEXT_KEY, False):
            args, kwargs = decompress_params(args, kwargs)

        # 设置上下文
        if hasattr(self, 'context') and self.context:
            set_context(self.context)

        is_log = kwargs.pop('__log', True)
        if is_log:
            rpc_log(func, self, *args, **kwargs)

        try:
            ret = func(self, *args, **kwargs)
        except exceptions.APIException as e:
            if isinstance(e.detail, (list, dict)):
                data = e.get_full_details()
            else:
                data = {'__global': e.get_full_details()}

            raise RestException(json.dumps(data))

        return ret

    return wrapper


def event_handler(*handler_args, **handler_kwargs):
    """
    添加自定义处理
    """
    def _event_handler(func):
        @base_event_handler(*handler_args, **handler_kwargs)
        @promise_db_connection
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 设置上下文
            if hasattr(self, 'context') and self.context:
                set_context(self.context)

            return func(self, *args, **kwargs)

        return wrapper

    return _event_handler
