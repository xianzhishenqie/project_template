import logging
import math
from collections import OrderedDict

from rest_framework import pagination, response
from rest_framework.utils.urls import replace_query_param


logger = logging.getLogger(__name__)

unlimit_number = 999999


class CacheLimitOffsetPaginationMixin(object):

    def get_count(self, queryset, view=None):
        if view and getattr(view, 'page_cache', False):
            cache_key = view._default_generate_count_cache_key()
            count = view.cache.get(cache_key)
            if count is None:
                count = self._get_count(queryset, view=view)
                view.cache.set(cache_key, count, view.get_cache_age())
        else:
            count = self._get_count(queryset, view=view)
        return count

    def get_limit(self, request, view=None):
        if hasattr(self, 'limit'):
            return self.limit
        limit = self._get_limit(request, view=view)
        if limit is None:
            if view and hasattr(view, 'unlimit_pagination') and view.unlimit_pagination:
                limit = unlimit_number
            else:
                limit = self.max_limit
            request.query_params._mutable = True
            request.query_params[self.limit_query_param] = limit
            request.query_params._mutable = False
        return limit

    def get_offset(self, request, view=None):
        return self._get_offset(request, view=view)

    def paginate_queryset_flag(self, queryset, request, view=None):
        self.queryset = queryset
        self.limit = self.get_limit(request, view)
        self.offset = self.get_offset(request, view)
        self.count = self.get_count(queryset, view)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []

        queryset = queryset[self.offset:self.offset + self.limit]
        if view and getattr(view, 'page_cache', False):
            self.page_queryset = queryset
            view.cache_key = view.get_cache_key()

        return True


class BootstrapPagination(pagination.LimitOffsetPagination):
    max_limit = 1000

    def get_paginated_response(self, data):
        return response.Response(OrderedDict([
            ('total', self.count),
            ('rows', data)
        ]))


class CacheBootstrapPagination(CacheLimitOffsetPaginationMixin, BootstrapPagination):

    def _get_count(self, queryset, view=None):
        try:
            return BootstrapPagination.get_count(self, queryset)
        except Exception as e:
            logger.error('get count error: %s', e.message)
            return len(queryset)

    def _get_limit(self, request, view=None):
        return BootstrapPagination.get_limit(self, request)

    def _get_offset(self, request, view=None):
        return BootstrapPagination.get_offset(self, request)



class VueTablePagination(pagination.LimitOffsetPagination):
    page_query_param = 'page'

    page_size_query_param = 'per_page'

    max_page_size = 1000

    def get_page_number(self, request, view=None):
        return pagination._positive_int(
            request.query_params.get(self.page_query_param, 1),
            strict=True
        )

    def get_page_size(self, request, view=None):
        page_size = request.query_params.get(self.page_size_query_param)
        if page_size is None:
            if view and hasattr(view, 'unlimit_pagination') and view.unlimit_pagination:
                page_size = unlimit_number
            else:
                page_size = self.max_page_size
        return pagination._positive_int(
            page_size,
            strict=True,
        )

    def get_limit(self, request, view=None):
        return self.get_page_size(request, view=view)

    def get_offset(self, request, view=None):
        self.page_number = self.get_page_number(request, view=view)
        self.limit = self.get_limit(request, view=view)
        return (self.page_number - 1) * self.limit

    def get_next_link(self):
        if self.page_number * self.limit >= self.count:
            return None
        url = self.request.build_absolute_uri()
        return replace_query_param(url, self.page_query_param, self.page_number + 1)

    def get_previous_link(self):
        if self.page_number == 1:
            return None
        url = self.request.build_absolute_uri()
        return replace_query_param(url, self.page_query_param, self.page_number - 1)

    def get_paginated_response(self, data):
        total = self.count
        page_size = self.limit
        page_number = self.page_number
        last_page = int(math.ceil(total * 1.0 / page_size))
        start = (page_number - 1) * page_size + 1
        end = start + page_size - 1
        return response.Response(OrderedDict([
            ('links', {
                'pagination': {
                    'total': total,
                    'per_page': page_size,
                    'current_page': page_number,
                    'last_page': last_page,
                    'next_page_url': self.get_next_link(),
                    'prev_page_url': self.get_previous_link(),
                    'from': start,
                    'to': end,
                }
            }),
            ('data', data)
        ]))


class CacheVueTablePagination(CacheLimitOffsetPaginationMixin, VueTablePagination):

    def _get_count(self, queryset, view=None):
        try:
            return VueTablePagination.get_count(self, queryset)
        except Exception as e:
            logger.error('get count error: %s', e.message)
            return len(queryset)

    def _get_limit(self, request, view=None):
        return VueTablePagination.get_limit(self, request, view=view)

    def _get_offset(self, request, view=None):
        return VueTablePagination.get_offset(self, request, view=view)
