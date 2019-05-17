import pickle

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sv_base.utils.base.text import ec
from sv_base.utils.base.type import NameInt
from sv_base.extensions.db.models import IntChoice


class Executor(models.Model):
    """
    序列化执行任务 func执行函数  params执行参数 context执行上下文
    """
    func = models.TextField()
    params = models.TextField(default='', blank=True)
    context = models.TextField(default='', blank=True)

    create_time = models.DateTimeField(default=timezone.now)

    @classmethod
    def add_executor(cls, executor):
        condition = cls.dump_executor(executor)
        return cls.objects.create(**condition)

    @classmethod
    def dump_executor(cls, executor):
        func = executor.get('func')
        if not callable(func):
            raise Exception(f'not callable function: {func}')

        params = executor.get('params', {})

        condition = {
            'func': pickle.dumps(func),
            'params': pickle.dumps(params),
        }
        return condition

    def load_executor(self):
        executor = {
            'func': pickle.loads(ec(self.func)),
            'params': pickle.loads(ec(self.params)) if self.params else {},
        }
        return executor

    def execute(self, *args, **kwargs):
        executor = self.load_executor()
        func = executor['func']
        params = executor['params']
        params.update(kwargs)
        return func(*args, **params)


class Event(models.Model):
    """
    事件记录表
    """
    event = models.PositiveIntegerField(_('x_event'), default=0)  # 事件, 覆盖此定义

    class Status(IntChoice):
        IN_PROGRESS = NameInt(1, _('x_in_progress'))
        OVER = NameInt(2, _('x_over'))
        ABNORMAL = NameInt(3, _('x_abnormal'))
    status = models.PositiveIntegerField(_('x_status'), choices=Status.choices())
    progress_code = models.PositiveIntegerField(_('x_progress_code'), default=0)
    progress_desc = models.CharField(_('x_progress_desc'), max_length=1024, blank=True, default='')

    class Meta:
        abstract = True
