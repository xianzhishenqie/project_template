"""
Provides generic filtering backends that can be used to filter the results
returned by list views.
"""
from __future__ import unicode_literals

import operator
from functools import reduce

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import ORDER_PATTERN
from django.utils import six

from rest_framework.compat import distinct


class BaseFilterBackend(object):
    """
    A base class from which all filter backend classes should inherit.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """
        raise NotImplementedError(".filter_queryset() must be overridden.")


class SearchFilter(BaseFilterBackend):
    # The URL query parameter used for the search.
    search_param = 'search'
    lookup_prefixes = {
        '^': 'istartswith',
        '=': 'iexact',
        '@': 'search',
        '$': 'iregex',
    }

    def get_search_fields(self, service, query_params):
        """
        Search fields are obtained from the service, but the request is always
        passed to this method. Sub-classes can override this method to
        dynamically change the search fields based on request content.
        """
        return getattr(service, 'search_fields', None)

    def get_search_terms(self, query_params):
        """
        Search terms are set by a ?search=... query parameter,
        and may be comma and/or whitespace delimited.
        """
        params = query_params.get(self.search_param, '')
        return params.replace(',', ' ').split()

    def construct_search(self, field_name):
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            lookup = 'icontains'
        return LOOKUP_SEP.join([field_name, lookup])

    def must_call_distinct(self, queryset, search_fields):
        """
        Return True if 'distinct()' should be used to query the given lookups.
        """
        for search_field in search_fields:
            opts = queryset.model._meta
            if search_field[0] in self.lookup_prefixes:
                search_field = search_field[1:]
            # Annotated fields do not need to be distinct
            if isinstance(queryset, models.QuerySet) and search_field in queryset.query.annotations:
                return False
            parts = search_field.split(LOOKUP_SEP)
            for part in parts:
                field = opts.get_field(part)
                if hasattr(field, 'get_path_info'):
                    # This field is a relation, update opts to follow the relation
                    path_info = field.get_path_info()
                    opts = path_info[-1].to_opts
                    if any(path.m2m for path in path_info):
                        # This field is a m2m relation so we know we need to call distinct
                        return True
        return False

    def filter_queryset(self, query_params, queryset, service):
        search_fields = self.get_search_fields(service, query_params)
        search_terms = self.get_search_terms(query_params)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(six.text_type(search_field))
            for search_field in search_fields
        ]

        base = queryset
        conditions = []
        for search_term in search_terms:
            queries = [
                models.Q(**{orm_lookup: search_term})
                for orm_lookup in orm_lookups
            ]
            conditions.append(reduce(operator.or_, queries))
        queryset = queryset.filter(reduce(operator.and_, conditions))

        if self.must_call_distinct(queryset, search_fields):
            # Filtering against a many-to-many field requires us to
            # call queryset.distinct() in order to avoid duplicate items
            # in the resulting queryset.
            # We try to avoid this if possible, for performance reasons.
            queryset = distinct(queryset, base)
        return queryset


class SearchSpecificFieldsFilter(SearchFilter):
    """
    根据指定字段模糊查询 'search_field'
    """
    search_delimiter = '_'

    def get_search_fields_terms(self, search_fields, query_params):
        """
        获取查询字段和输入值
        :param search_fields: 查询字段
        :param query_params: 查询参数
        :return: 搜索内容
        """
        if not search_fields:
            return None

        prefix_length = len(self.search_param) + len(self.search_delimiter)
        # 获取查询字段和输入值
        params = {}
        for field in search_fields:
            param = query_params.get(field)
            if not param:
                continue

            params.setdefault(field[prefix_length:], param.replace(',', ' ').split())

        return params

    def get_search_params(self, service):
        """
        获取search_fields结构的搜索字段
        :param service: 服务
        :return:
        """
        search_fields = getattr(service, 'search_fields', None)
        if not search_fields:
            return search_fields

        return [f'{self.search_param}{self.search_delimiter}{field}' for field in search_fields]

    def filter_queryset(self, query_params, queryset, service):
        """
        过滤查询集
        :param query_params: 查询参数
        :param queryset: 查询集
        :param service: 服务
        :return: 查询集
        """
        # 获取可查询的字段列表
        search_fields = self.get_search_params(service)

        if not search_fields:
            return queryset

        # 获取查询字段和输入值
        search_field_terms = self.get_search_fields_terms(search_fields, query_params)

        base = queryset
        conditions = []
        # 组合查询
        for search_field, search_terms in search_field_terms.items():
            orm_lookup = self.construct_search(six.text_type(search_field))
            queries = [
                models.Q(**{orm_lookup: search_term})
                for search_term in search_terms
            ]
            conditions.append(reduce(operator.or_, queries))

        if conditions:
            queryset = queryset.filter(reduce(operator.and_, conditions))

        if self.must_call_distinct(queryset, self.get_search_fields(service, query_params)):
            queryset = distinct(queryset, base)

        return queryset


class OrderingFilter(BaseFilterBackend):
    # The URL query parameter used for the ordering.
    ordering_param = 'sort'
    ordering_fields = None

    def get_ordering(self, query_params, queryset, service):
        """
        Ordering is set by a comma delimited ?ordering=... query parameter.

        The `ordering` query parameter can be overridden by setting
        the `ordering_param` value on the OrderingFilter or by
        specifying an `ORDERING_PARAM` value in the API settings.
        """
        params = query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            ordering = self.remove_invalid_fields(queryset, fields, service, query_params)
            if ordering:
                return ordering

        # No ordering was included, or all the ordering fields were invalid
        return self.get_default_ordering(service)

    def get_default_ordering(self, service):
        ordering = getattr(service, 'ordering', None)
        if isinstance(ordering, six.string_types):
            return (ordering,)
        return ordering

    def get_default_valid_fields(self, queryset, service, context={}):
        # If `ordering_fields` is not specified, then we determine a default
        # based on the serializer class, if one exists on the view.
        if hasattr(service, 'get_serializer_class'):
            try:
                serializer_class = service.get_serializer_class()
            except AssertionError:
                # Raised by the default implementation if
                # no serializer_class was found
                serializer_class = None
        else:
            serializer_class = getattr(service, 'serializer_class', None)

        if serializer_class is None:
            msg = (
                "Cannot use %s on a view which does not have either a "
                "'serializer_class', an overriding 'get_serializer_class' "
                "or 'ordering_fields' attribute."
            )
            raise ImproperlyConfigured(msg % self.__class__.__name__)

        return [
            (field.source.replace('.', '__') or field_name, field.label)
            for field_name, field in serializer_class(context=context).fields.items()
            if not getattr(field, 'write_only', False) and not field.source == '*'
        ]

    def get_valid_fields(self, queryset, service, context={}):
        valid_fields = getattr(service, 'ordering_fields', self.ordering_fields)

        if valid_fields is None:
            # Default to allowing filtering on serializer fields
            return self.get_default_valid_fields(queryset, service, context)

        elif valid_fields == '__all__':
            # View explicitly allows filtering on any model field
            valid_fields = [
                (field.name, field.verbose_name) for field in queryset.model._meta.fields
            ]
            valid_fields += [
                (key, key.title().split('__'))
                for key in queryset.query.annotations
            ]
        else:
            valid_fields = [
                (item, item) if isinstance(item, six.string_types) else item
                for item in valid_fields
            ]

        return valid_fields

    def remove_invalid_fields(self, queryset, fields, service, query_params):
        valid_fields = [item[0] for item in self.get_valid_fields(queryset, service, {})]
        return [term for term in fields if term.lstrip('-') in valid_fields and ORDER_PATTERN.match(term)]

    def filter_queryset(self, query_params, queryset, service):
        ordering = self.get_ordering(query_params, queryset, service)

        if ordering:
            return queryset.order_by(*ordering)

        return queryset
