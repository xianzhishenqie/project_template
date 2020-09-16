import logging
import sys
import time
from socket import timeout

import functools
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import QuerySet
from django.utils import translation
from django_nameko.rpc import get_pool
from nameko.constants import LANGUAGE_CONTEXT_KEY
from nameko.events import BROADCAST, EventDispatcher

from sv_base.extensions.db.models import STATUS_DELETED
from sv_base.extensions.rest.request import DataFilter
from sv_base.extensions.service import filters
from sv_base.extensions.service.contextdata import ContextData
from sv_base.extensions.service.rpc import (rpc, get_context, event_handler as base_event_handler, compress_params,
                                            COMPRESS_CONTEXT_KEY)
from sv_base.utils.base.text import rk
from sv_base.utils.base.thread import async_exe

logger = logging.getLogger(__name__)

TIMESTAMP_CONTEXT_KEY = 'timestamp'
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
DEFAULT_POOL_NAME = 'default'


class ServiceBase:
    context = ContextData()


class ServiceCommon(ServiceBase):
    """
    通用数据对象服务基础类
    """
    name = 'service_common'
    # 数据索引字段名称
    key_name = 'resource_id'
    # 序列化类
    serializer_class = None
    # 物理删除
    physically_delete = True

    search_fields = None
    enable_search_specific_fields = False
    enable_ordering = True
    ordering_fields = None
    ordering = None

    @rpc
    def get(self, key, fields=None, context=None):
        """
        获取单条数据
        :param key: 数据索引值
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :return: 数据
        """
        instance = self.get_instance(key)
        if not instance:
            return None

        serializer = self.get_serializer_class()(instance=instance, fields=fields, context=context or {})

        return serializer.data

    @rpc
    def batch_get(self, keys, fields=None, context=None):
        """
        获取多条数据
        :param keys: 数据索引值列表
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :return: 数据
        """
        instances = self.get_instances_by_keys(keys)

        serializer = self.get_serializer_class()(instances, fields=fields, many=True, context=context or {})

        return serializer.data

    @rpc
    def get_list(self, query_params=None, fields=None, context=None, with_total=False):
        """
        获取多条数据
        :param query_params: 查询参数
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :param with_total: 查询总数
        :return: 多条数据
        """
        query_params = {} if query_params is None else query_params
        self.query_data = DataFilter(query_params)

        instances = self.get_instances(query_params)

        if isinstance(instances, QuerySet):
            if self.search_fields:
                instances = filters.SearchFilter().filter_queryset(query_params, instances, self)

            if self.enable_search_specific_fields:
                # 模糊查询指定字段 search_field
                instances = filters.SearchSpecificFieldsFilter().filter_queryset(query_params, instances, self)

            if self.enable_ordering:
                instances = filters.OrderingFilter().filter_queryset(query_params, instances, self)

        if with_total:
            total = instances.count() if isinstance(instances, QuerySet) else len(instances)

        instances = self.get_page_instances(instances, query_params)

        serializer = self.get_serializer_class()(instances, fields=fields, many=True, context=context or {})

        if with_total:
            data = {
                'data': serializer.data,
                'total': total,
            }
        else:
            data = serializer.data

        return data

    @rpc
    def create(self, data, fields=None, context=None):
        """
        创建数据
        :param data: 数据内容
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :return: 数据内容
        """
        serializer = self.get_serializer_class()(data=data, fields=fields, context=context or {})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return serializer.data

    @rpc
    def batch_create(self, data, fields=None, context=None):
        """
        批量创建数据，效率较低
        :param data: 数据内容列表
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :return: 数据内容
        """
        serializer_class = self.get_serializer_class()
        serializers = []
        for row in data:
            serializer = serializer_class(data=row, fields=fields, context=context or {})
            serializer.is_valid(raise_exception=True)
            serializers.append(serializer)

        with transaction.atomic(savepoint=False):
            for serializer in serializers:
                serializer.save()

        return [serializer.data for serializer in serializers]

    @rpc
    def simple_batch_create(self, data, fields=None, context=None, batch_size=None, is_return=False):
        """
        简单单表批量创建数据，不存在关联数据的创建、更新和校验，效率较高
        :param data: 数据内容列表
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :param batch_size: 每次批量数量
        :param is_return: 是否返回序列化结果
        :return: 数据内容
        """
        model_class = self.get_model_class()
        objs = []
        for row in data:
            obj = model_class(**row)
            objs.append(obj)

        objs = model_class.objects.bulk_create(objs, batch_size=batch_size)

        if is_return:
            serializer_class = self.get_serializer_class()
            serializer = serializer_class(objs, many=True, fields=fields, context=context or {})
            return serializer.data
        else:
            return True

    @rpc
    def update(self, data, fields=None, context=None):
        """
        更新数据
        :param data: 更新的数据内容
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :return: 数据内容
        """
        key = data.pop(self.key_name, None)
        instance = self.get_instance(key)
        if not instance:
            return None

        serializer = self.get_serializer_class()(instance=instance, data=data, fields=fields, partial=True,
                                                 context=context or {})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return serializer.data

    @rpc
    def batch_update(self, data, fields=None, context=None):
        """
        批量更新数据
        :param data: 数据内容列表
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :return: 数据内容
        """
        key_row = {}
        for row in data:
            key = row.pop(self.key_name, None)
            if not key:
                raise ValueError(f'row has no key[{self.key_name}] value: {row}')

            key_row[key] = row

        instances = self.get_instances_by_keys(list(key_row.keys()))
        key_data = {}
        for instance in instances:
            key = getattr(instance, self.key_name)
            row = key_row.pop(key, None)
            if row:
                key_data[key] = (instance, row)

        if key_row:
            keys = list(key_row.keys())
            raise ValueError(f'rows has no associated instances: {keys}')

        serializer_class = self.get_serializer_class()
        serializers = []
        for key, (instance, row) in key_data.items():
            serializer = serializer_class(instance=instance, data=row, fields=fields, partial=True,
                                          context=context or {})
            serializer.is_valid(raise_exception=True)
            serializers.append(serializer)

        with transaction.atomic(savepoint=False):
            for serializer in serializers:
                serializer.save()

                if getattr(serializer.instance, '_prefetched_objects_cache', None):
                    serializer.instance._prefetched_objects_cache = {}

        return [serializer.data for serializer in serializers]

    @rpc
    def simple_batch_update(self, data, fields=None, context=None, batch_size=None, is_return=False):
        """
        简单单表批量更新数据，不存在关联数据的创建、更新和校验，效率较高
        :param data: 数据内容列表
        :param fields: 想要获取的数据字段
        :param context: 序列化上下文
        :param batch_size: 每次批量数量
        :param is_return: 是否返回序列化结果
        :return: 数据内容
        """
        model_class = self.get_model_class()
        objs = []
        for row in data:
            obj = model_class(**row)
            objs.append(obj)

        if data:
            bulk_update_fields = [name for name in list(data[0].keys())
                                  if not model_class._meta.get_field(name).primary_key]
            objs = model_class.objects.bulk_update(objs, fields=bulk_update_fields, batch_size=batch_size)

        if is_return:
            serializer_class = self.get_serializer_class()
            serializer = serializer_class(objs, many=True, fields=fields, context=context or {})
            return serializer.data
        else:
            return True

    @rpc
    def delete(self, key):
        """
        删除数据
        :param key: 数据索引值
        :return: 删除的索引值
        """
        instance = self.get_instance(key)
        if not instance:
            return None

        self._delete_instance(instance)

        return key

    @rpc
    def batch_delete(self, keys):
        """
        批量删除数据
        :param key: 数据索引值列表
        :return: 删除的索引值列表
        """
        instances = self.get_instances_by_keys(keys)

        deleted_keys = []
        for instance in instances:
            self._delete_instance(instance)
            deleted_keys.append(getattr(instance, self.key_name))

        return deleted_keys

    def _delete_instance(self, instance):
        """
        删除实例
        :param instance: 实例对象
        :return: 无
        """
        if self.physically_delete:
            instance.delete()
        else:
            instance.status = STATUS_DELETED
            instance.save()

    def get_model_class(self):
        """
        获取model类
        :return: model类
        """
        model_class = getattr(self, 'model_class', None)
        if not model_class:
            serializer_class = self.get_serializer_class()
            if serializer_class:
                serializer_class_meta = getattr(serializer_class, 'Meta', None)
                if serializer_class_meta:
                    model_class = getattr(serializer_class_meta, 'model', None)

        if not model_class:
            return Exception('cannot find valid model class')

        return model_class

    def get_serializer_class(self):
        """
        获取序列化类
        :return: 序列化类
        """
        serializer_class = getattr(self, 'serializer_class', None)
        if not serializer_class:
            return Exception('cannot find valid serializer class')

        return serializer_class

    def get_instance(self, key):
        """
        获取实例对象
        :param key: 实例key
        :return: 实例对象
        """
        if key:
            model_class = self.get_model_class()
            instance = model_class.objects.filter(**{self.key_name: key}).first()
        else:
            instance = None

        return instance

    def get_instances_by_keys(self, keys):
        """
        获取实例集合
        :param keys: 实例keys
        :return: 实例集合
        """
        if keys:
            model_class = self.get_model_class()
            instances = model_class.objects.filter(**{f'{self.key_name}__in': keys})
        else:
            instances = []

        return instances

    def get_instances(self, query_params):
        """
        获取查询实例集合
        :param query_params: 查询参数
        :return: 查询实例集合
        """
        queryset = self.get_model_class().objects.all()

        exclude = query_params.get('exclude')
        if exclude:
            if not isinstance(exclude, list):
                exclude = [exclude]

            queryset = queryset.exclude(**{f'{self.key_name}__in': exclude})

        return queryset

    def get_page_instances(self, instances, query_params):
        """
        分页处理查询处理
        :param instances: 查询集合
        :param query_params: 查询参数
        :return: 查询处理结果集合
        """
        query_data = DataFilter(query_params)
        page_flag = query_data.get('page_flag', bool, True)
        if page_flag:
            page = query_data.get('page', int, DEFAULT_PAGE)
            page_size = query_data.get('per_page', int, DEFAULT_PAGE_SIZE)
            end = page * page_size
            start = end - page_size
            instances = instances[start:end]

        return instances


class EventSender(ServiceBase):
    name = 'event_sender'
    dispatch = EventDispatcher()

    @rpc
    def send(self, key, data, timeout=None):
        options = {}
        if timeout:
            options['expiration'] = timeout

        self.dispatch(key, data, **options)


def send_event(key, data, timeout=None, **kwargs):
    """
    发送事件
    :param key: 事件识别key
    :param data: 消息数据
    :param timeout: 消息过期时间
    """
    get_service('event_sender').send(key, data, timeout=timeout, __log=False, **kwargs)


def event_handler(*handler_args, **handler_kwargs):
    """
    默认event_sender
    """
    def _event_handler(func):
        @base_event_handler('event_sender', *handler_args, **handler_kwargs)
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    return _event_handler


broadcast_event_handler = functools.partial(event_handler, handler_type=BROADCAST, reliable_delivery=False)


class SocketServiceCommonBase(type):
    """
    通用rpc socket代理服务元类，添加事件接收
    """
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)

        if cls.listen_routing_key:
            @broadcast_event_handler(cls.listen_routing_key)
            def listen(self, data):
                self.receive_listen(data)

            cls.listen = listen

        if cls.send_routing_key:
            @broadcast_event_handler(cls.send_routing_key)
            def send(self, data):
                self.receive_send(data)

            cls.send = send

        if cls.close_routing_key:
            @broadcast_event_handler(cls.close_routing_key)
            def close(self, data):
                self.receive_send(data)

            cls.close = close

        return cls


class SocketServiceCommon(ServiceBase, metaclass=SocketServiceCommonBase):
    """
    通用rpc socket代理服务
    """
    name = 'socket_service_common'
    listen_routing_key = ''
    send_routing_key = ''
    close_routing_key = ''
    socket_timeout = 300
    recv_size = 1024
    socket_pool = {}

    def _connect(self, key):
        """
        连接得到socket对象
        :param key: 调用key
        :return: socket对象
        """
        pass

    def _send(self, key, connection_id, data):
        """
        代理socket接受数据, 一般send_message
        :param key: 调用key
        :param data: 数据
        :return: 无
        """
        pass

    def _before_close(self, key, sock):
        """
        自定义关闭逻辑
        :param key:调用key
        :param sock:未关闭的sock对象
        :return: 无
        """
        pass

    def _after_close(self, key, sock):
        """
        自定义关闭逻辑
        :param key:调用key
        :param sock:已关闭的sock对象
        :return: 无
        """
        pass

    def _listen(self, key, connection_id):
        """
        监听消息
        :param key: 调用key
        :return: 无
        """
        sock = self.get_socket(connection_id)

        if not sock or sock._listening:
            return

        sock._listening = True
        sock._stopping = False
        sock.settimeout(self.socket_timeout)
        while True:
            if sock._stopping:
                break

            try:
                resp = sock.recv(self.recv_size)
                if resp is not None:
                    self._send(key, connection_id, str(resp, encoding='utf-8', errors="ignore"))
                else:
                    logger.info("service daemon socket is close")
            except timeout:
                logger.warning('Receive from service socket timeout.')
                break
            except OSError:
                logger.warning("service daemon socket err: EAGAIN")
            except Exception as e:
                logger.error("service daemon socket err: %s" % e)
                break

        self.clear_socket(key)

    def create_socket(self, key):
        """
        获取socket对象
        :param key: 调用key
        :return: socket对象
        """
        sock = self._connect(key)
        if sock:
            connection_id = rk()
            sock._connection_id = connection_id
            sock._listening = False
            sock._stopping = False
            self.socket_pool[connection_id] = sock

        return sock

    def get_socket(self, connection_id):
        """
        获取socket对象
        :param connection_id: 连接id
        :return: socket对象
        """
        return self.socket_pool.get(connection_id)

    def clear_socket(self, connection_id):
        """
        清除socket对象
        :param connection_id: 连接id
        :return: 无
        """
        sock = self.socket_pool.pop(connection_id, None)
        if sock:
            sock._listening = False
            sock._stopping = True
            sock.close()

        return sock

    def check_connection(self, data):
        key = data.get('key')
        connection_id = data.get('connection_id')
        if not key or not connection_id:
            return False

        return self.get_socket(connection_id)

    @rpc
    def connect(self, key):
        """
        rpc代理连接
        :param key: 调用key
        :return: 连接id
        """
        sock = self.create_socket(key)
        return sock._connection_id

    def receive_listen(self, data):
        """
        rpc代理监听
        :param key: 调用key
        :return: 连接id
        """
        sock = self.check_connection(data)
        if not sock:
            return False

        key = data.get('key')
        async_exe(self._listen, (key, sock._connection_id))

        return True

    def receive_send(self, data):
        """
        rpc代理发送数据
        :param data: 数据
        :return: 无
        """
        content = data.get('data')
        if content is None:
            return

        sock = self.check_connection(data)
        if not sock:
            return

        key = data.get('key')
        async_exe(self._listen, (key, sock._connection_id))

        sock.sendall(content)

    def receive_close(self, data):
        """
        rpc代理关闭连接
        :param data: 数据
        :return: 无
        """
        sock = self.check_connection(data)
        if not sock:
            return

        key = data.get('key')
        self._before_close(key, sock)
        self.clear_socket(sock._connection_id)
        self._after_close(key, sock)


class RpcProxy:
    """
    rpc客户端代理
    """

    def __init__(self):
        self._proxy = get_pool().next()

    def __enter__(self):
        self._proxy.__enter__()
        return self

    def __exit__(self, tpe=None, value=None, traceback=None):
        self._proxy.__exit__(tpe, value, traceback)

    def __getattr__(self, name):
        return ServiceProxy(self, getattr(self._proxy, name))

    def set_context(self, context=None):
        worker_ctx = self._proxy._proxy._worker_ctx
        worker_ctx._origin_data = worker_ctx.data
        context_data = worker_ctx.data.copy()
        # 设置默认上下文
        context_data.update({
            TIMESTAMP_CONTEXT_KEY: time.time(),
            LANGUAGE_CONTEXT_KEY: translation.get_language(),
        })

        # 设置当前上下文
        context_data.update(get_context())

        # 设置自定义上下文
        context = context or {}
        context_data.update(context)
        worker_ctx.data = context_data

    def del_context(self):
        worker_ctx = self._proxy._proxy._worker_ctx
        if hasattr(worker_ctx, '_origin_data'):
            worker_ctx.data = worker_ctx._origin_data
            del worker_ctx._origin_data


class ServiceProxy:
    """
    rpc service代理
    """
    def __init__(self, rpc_proxy, service_proxy):
        self._rpc_proxy = rpc_proxy
        self._service_proxy = service_proxy

    def __enter__(self):
        return self

    def __exit__(self, tpe=None, value=None, traceback=None):
        self._rpc_proxy.__exit__(tpe, value, traceback)

    def __getattr__(self, name):
        return MethodProxy(self._rpc_proxy, self, getattr(self._service_proxy, name))


class MethodProxy:
    """
    rpc service方法代理
    """

    def __init__(self, rpc_proxy, service_proxy, method):
        self._rpc_proxy = rpc_proxy
        self._service_proxy = service_proxy
        self._method = method

    def __enter__(self):
        return self

    def __exit__(self, tpe=None, value=None, traceback=None):
        self._rpc_proxy.__exit__(tpe, value, traceback)

    def __call__(self, *args, **kwargs):
        return self._call(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._method, name)

    def _log(self, *args, **kwargs):
        msg = f'[RPC CALLING] {self.service_name}:{self.method_name}, args: {args}, kwargs: {kwargs}, ' \
              f'context: {self.worker_ctx.data}'
        logger.debug(msg)

    def _call(self, *args, **kwargs):
        context = kwargs.pop('__context', None)
        self._rpc_proxy.set_context(context)

        call_once = kwargs.pop('__once', True)
        is_async = kwargs.pop('__async', False)
        is_log = kwargs.get('__log', True)
        if is_log:
            self._log(*args, **kwargs)

        if self.worker_ctx.data.get(COMPRESS_CONTEXT_KEY):
            args, kwargs = compress_params(args, kwargs)

        try:
            if is_async:
                ret = self._method.call_async(*args, **kwargs)
            else:
                ret = self._method(*args, **kwargs)
        except Exception as e:
            self._rpc_proxy.del_context()
            self.__exit__(type(e), e, None)
            raise
        else:
            self._rpc_proxy.del_context()
            if call_once:
                self.__exit__()

            return ret

    def call_async(self, *args, **kwargs):
        kwargs['__async'] = True
        return self._call(*args, **kwargs)


def get_service(service_name):
    """
    获取服务对象
    :param service_name: 服务名称
    :return: 服务对象
    """
    rpc_proxy = RpcProxy()
    rpc_proxy.__enter__()
    return getattr(rpc_proxy, service_name)


def module_service(invoker_mapping, module_name):
    """
    模块直接调用服务装饰器
    :param invoker_mapping: 调用变量名称和服务名称映射
    :param module_name: 调用模块名称
    :return: 模块直接调用服务装饰器
    """
    module = sys.modules[module_name]

    def _module_service(get_attr_func):
        """
        模块直接调用服务装饰器
        :param get_attr_func: 模块__get_attr__方法
        :return: 装饰模块__get_attr__方法
        """
        @functools.wraps(get_attr_func)
        def wrapper(name):
            if name in invoker_mapping:
                service_name = invoker_mapping[name]
                return get_service(service_name)

            try:
                return get_attr_func(name)
            except AttributeError:
                if name not in dir(module):
                    raise AttributeError(f'module {module.__name__} has no attribute {name}')

        return wrapper

    return _module_service


def format_nameko_config(nameko_config):
    """
    格式化统一的nameko配置
    {
        'default': config,
        ...
    }
    :param nameko_config: 原始namkeko配置
    :return: 统一格式的nameko配置
    """

    if DEFAULT_POOL_NAME in nameko_config:
        return nameko_config
    else:
        return {
            DEFAULT_POOL_NAME: nameko_config,
        }


def get_config(nameko_config, name=None):
    """
    获取nameko配置
    :param nameko_config: 原始namkeko配置
    :param name: nameko配置名称
    :return: nameko配置
    """
    name = name or DEFAULT_POOL_NAME
    nameko_config_pool = format_nameko_config(nameko_config)
    if name not in nameko_config_pool:
        raise ImproperlyConfigured(f'NAMEKO_CONFIG has no config {name}')

    return nameko_config_pool[name]
