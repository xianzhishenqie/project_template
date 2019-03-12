from django.db.models import QuerySet

from sv_base.utils.rest.mixins import BatchSetModelMixin

from sv_auth.models import Owner
from sv_auth.utils.owner import filter_operate_queryset


class BatchSetOwnerModelMixin(BatchSetModelMixin):
    """
    批量更新资源字段
    """
    batch_set_fields = {
        'public_mode': Owner.PublicMode.__members__.values()
    }

    def perform_batch_set(self, queryset: QuerySet, field: str, value: object) -> bool:
        """批量更新字段。

        :param queryset: 更新集
        :param field: 更新字段
        :param value: 更新值
        :return: 有更新True 无更新False
        """
        queryset = filter_operate_queryset(self.request.user, queryset)
        return super(BatchSetOwnerModelMixin, self).perform_batch_set(queryset, field, value)
