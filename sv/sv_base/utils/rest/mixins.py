from __future__ import annotations
import json

from django.conf import settings
from django.db.models import Model, QuerySet
from django.db.models.sql.datastructures import EmptyResultSet
from django.utils import six
from django.utils.module_loading import import_string

from rest_framework import exceptions, mixins, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from sv_base.utils.common.ucache import CacheProduct, delete_cache
from sv_base.utils.common.utext import md5
from sv_base.utils.rest.pagination import VueTablePagination, CacheVueTablePagination
from sv_base.utils.rest.request import RequestData


class SVMixin:
    """
    项目viewset公共继承类， 添加了请求字段过滤，合法数据过滤功能
    """
    pagination_class = VueTablePagination

    def initial(self, request: Request, *args, **kwargs) -> None:
        """初始化viewset request

        :param request: 请求对象
        :param args: 其他参数
        :param kwargs: 其他参数
        """
        # 查询条件
        self.query_data = RequestData(request, is_query=True)
        # 修改条件
        self.shift_data = RequestData(request, is_query=False)
        # 查询字段
        self.query_data_fields = self.query_data.getlist('_fields')
        super(SVMixin, self).initial(request, *args, **kwargs)

    def get_serializer(self, *args, **kwargs) -> Serializer:
        """获取rest序列化数据对象

        :param args: 其他参数
        :param kwargs: 其他参数
        :return: rest序列化数据对象
        """
        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        kwargs['context'] = context
        if self.query_data_fields:
            kwargs['fields'] = self.query_data_fields
        return serializer_class(*args, **kwargs)


def _generate_cache_key(view, queryset):
    view_name = view.__class__.__name__
    try:
        key_str = queryset.query.__str__()
    except EmptyResultSet:
        # 无查询的空对象
        key_str = 'EmptyResultSet'

    query_data_fields = getattr(view, 'query_data_fields', [])
    query_data_fields.sort()
    key_str = '%s:%s' % (key_str, md5(json.dumps(query_data_fields)))

    cache_key_prefix = view.get_cache_key_prefix()
    if cache_key_prefix is not None:
        key_str = '%s:%s' % (cache_key_prefix, key_str)

    return md5('%s:%s' % (view_name, key_str))


def _generate_cache_view_name(view_cls):
    return "%s-%s" % (view_cls.__module__, view_cls.__name__)


class CacheModelMixin:
    """
    viewset缓存混入类
    """
    pagination_class = CacheVueTablePagination
    page_cache = True

    def __new__(cls, *args, **kwargs) -> CacheModelMixin:
        obj = super(CacheModelMixin, cls).__new__(cls)
        view_name = _generate_cache_view_name(cls)
        obj.cache = CacheProduct(view_name)

        return obj

    def _default_generate_cache_key(self):
        return _generate_cache_key(self, self.paginator.page_queryset)

    def _default_generate_count_cache_key(self):
        return _generate_cache_key(self, self.paginator.queryset)

    def get_cache_key_prefix(self):
        return None

    def get_cache_flag(self):
        return settings.ENABLE_API_CACHE and getattr(self, 'page_cache', False)

    def get_cache_key(self):
        if not hasattr(self, 'generate_cache_key'):
            return self._default_generate_cache_key()
        return self.generate_cache_key()

    def get_cache_age(self):
        return getattr(self, 'page_cache_age', settings.DEFAULT_CACHE_AGE)

    def clear_cache(self):
        delete_cache(self.cache)
        if hasattr(self, 'related_cache_classes'):
            self.clear_cls_cache(self.related_cache_classes)

    @classmethod
    def clear_self_cache(cls):
        cls.clear_cls_cache(cls)
        if hasattr(cls, 'related_cache_classes'):
            cls.clear_cls_cache(cls.related_cache_classes)

    @staticmethod
    def clear_cls_cache(cls):
        if not isinstance(cls, (list, tuple)):
            cls = [cls]
        for c in cls:
            if isinstance(c, (six.string_types, six.text_type)):
                try:
                    c = import_string(c)
                except Exception:
                    continue
            cache_view_name = _generate_cache_view_name(c)
            cache = CacheProduct(cache_view_name)
            delete_cache(cache)

    def paginate_queryset_flag(self, queryset: QuerySet) -> bool:
        """判断是否需要进行查询

        :param queryset: 查询queryset
        :return: bool
        """
        return self.paginator.paginate_queryset_flag(queryset, self.request, view=self)

    def list(self, request: Request, *args, **kwargs) -> list:
        """批量获取数据

        :param request: 请求对象
        :param args: 其他参数
        :param kwargs: 其他参数
        :return: 序列化数据列表
        """
        queryset = self.filter_queryset(self.get_queryset())
        paginate_queryset_flag = self.paginate_queryset_flag(queryset)
        if paginate_queryset_flag:
            if self.get_cache_flag():
                cache_value = self.cache.get(self.cache_key)
                if cache_value:
                    data = cache_value
                else:
                    data = self._get_list_data(queryset)
                    self.cache.set(self.cache_key, data, self.get_cache_age())
            else:
                data = self._get_list_data(queryset)
        else:
            data = []
        return self.get_paginated_response(data)

    def _get_list_data(self, queryset: QuerySet) -> list:
        """获取查询数据

        :param queryset: 查询queryset
        :return: 序列化结果
        """
        page = self.paginate_queryset(queryset)
        data = self.get_serializer(page, many=True).data
        data = self.extra_handle_list_data(data)
        return data

    @staticmethod
    def extra_handle_list_data(data: list) -> list:
        """额外处理返回数据

        :param data: 返回数据
        :return: 处理后数据
        """
        return data

    def perform_create(self, serializer: Serializer) -> None:
        """插入数据

        :param serializer: 数据序列化对象
        """
        if self.sub_perform_create(serializer):
            self.clear_cache()

    def perform_update(self, serializer: Serializer) -> None:
        """更新数据

        :param serializer: 数据序列化对象
        """
        if self.sub_perform_update(serializer):
            self.clear_cache()

    def perform_destroy(self, instance: Model) -> None:
        """删除数据

        :param instance: 数据对象
        """
        if self.sub_perform_destroy(instance):
            self.clear_cache()

    def sub_perform_create(self, serializer: Serializer) -> bool:
        """插入数据

        :param serializer: 数据序列化对象
        :return: 是否有插入
        """
        super(CacheModelMixin, self).perform_create(serializer)
        return True

    def sub_perform_update(self, serializer: Serializer) -> bool:
        """更新数据

        :param serializer: 数据序列化对象
        :return: 是否有更新
        """
        super(CacheModelMixin, self).perform_update(serializer)
        return True

    def sub_perform_destroy(self, instance: Model) -> bool:
        """删除数据

        :param instance: 数据对象
        :return: 是否有删除
        """
        super(CacheModelMixin, self).perform_destroy(instance)
        return True


class DestroyModelMixin(mixins.DestroyModelMixin):
    """
    批量删除数据混入类
    """
    def perform_destroy(self, instance: Model) -> None:
        """删除单挑数据

        :param instance: 数据实例
        """
        if self.sub_perform_destroy(instance) and hasattr(self, 'clear_cache'):
            self.clear_cache()

    def sub_perform_destroy(self, instance: Model) -> bool:
        """删除单挑数据具体实现

        :param instance: 数据实例
        """
        instance.status = instance.Status.DELETE
        instance.save()
        return True

    @action(methods=['delete'], detail=False)
    def batch_destroy(self, request: Request) -> Response:
        """删除多条数据

        :param request: 请求对象
        :return: 响应对象
        """
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        queryset = self.queryset.filter(id__in=ids)
        if self.perform_batch_destroy(queryset) and hasattr(self, 'clear_cache'):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_destroy(self, queryset: QuerySet) -> bool:
        """删除多条数据具体实现

        :param queryset: 多条数据queryset
        """
        if queryset.update(status=queryset.model.Status.DELETE) > 0:
            return True
        return False


class BatchSetModelMixin:
    """
    批量设置字段值混入类
    """
    batch_set_fields = {}

    @action(methods=['patch'], detail=False)
    def batch_set(self, request: Request) -> Response:
        """批量设置字段通用api

        :param request: 请求对象
        :return: 响应对象
        """
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_200_OK)

        field = self.shift_data.get('field')
        if field not in self.batch_set_fields:
            raise exceptions.PermissionDenied()

        filter_config = self.batch_set_fields[field]
        allow_null = False
        if isinstance(filter_config, dict):
            filter_params = filter_config.get('filter')
            allow_null = filter_config.get('null')
        else:
            filter_params = filter_config
        value = self.shift_data.get('value', filter_params)
        if value is None and not allow_null:
            raise exceptions.PermissionDenied()

        queryset = self.queryset.filter(id__in=ids)
        if self.perform_batch_set(queryset, field, value) and hasattr(self, 'clear_cache'):
            self.clear_cache()

        return Response(status=status.HTTP_200_OK)

    def perform_batch_set(self, queryset: QuerySet, field: str, value: object) -> bool:
        """批量设置字段通用更新

        :param queryset: 更新的queryset
        :param field: 字段名称
        :param value: 更新后的值
        :return: 是否有更新
        """
        if queryset.update(**{field: value}) > 0:
            return True
        return False
