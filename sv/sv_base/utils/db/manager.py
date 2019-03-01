from typing import Optional

from django.db import models


class MManager(models.Manager):
    """
    自定义数据模型管理器，支持默认过滤条件
    """
    def __init__(self, iexclude: Optional[dict] = None, ifilter: Optional[dict] = None) -> None:
        """初始化

        :param iexclude: 排除过滤条件
        :param ifilter: 过滤条件
        """
        super(MManager, self).__init__()
        self._inner_exclude = iexclude
        self._inner_filter = ifilter

    def get_queryset(self) -> models.QuerySet:
        queryset = super(MManager, self).get_queryset()
        if self._inner_exclude:
            queryset = queryset.exclude(**self._inner_exclude)
        if self._inner_filter:
            queryset = queryset.filter(**self._inner_filter)
        return queryset
