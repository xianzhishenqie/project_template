import pickle

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sv_base.extensions.db.manager import MManager
from sv_base.extensions.db.models import IntChoice, StrChoice
from sv_base.extensions.db.fields import RemoteFileField
from sv_base.extensions.resource.models import PrimaryResourceModel
from sv_base.utils.base.text import ec
from sv_base.utils.base.type import NameInt


class Executor(models.Model):
    """
    序列化执行任务 func执行函数  params执行参数 context执行上下文
    """
    func = models.BinaryField()
    params = models.BinaryField(default=b'', blank=True)
    context = models.BinaryField(default=b'', blank=True)

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
        START = NameInt(0, _('x_start'))
        IN_PROGRESS = NameInt(1, _('x_in_progress'))
        OVER = NameInt(2, _('x_over'))
        ABNORMAL = NameInt(3, _('x_abnormal'))

    status = models.PositiveIntegerField(_('x_status'), choices=Status.choices())
    progress_code = models.PositiveIntegerField(_('x_progress_code'), default=0)
    ProgressStatus = Status
    progress_status = models.PositiveIntegerField(_('x_progress_status'), choices=ProgressStatus.choices())
    progress_desc = models.CharField(_('x_progress_desc'), max_length=1024, blank=True, default='')
    source_progress_desc = models.CharField(_('x_progress_desc'), max_length=2048, blank=True, default='')
    create_time = models.DateTimeField(_('x_create_time'), default=timezone.now)

    class Meta:
        abstract = True


class Log(models.Model):
    """
    基础日志表
    """

    class Level(StrChoice):
        INFO = 'INFO'
        DEBUG = 'DEBUG'
        WARNING = 'WARNING'
        ERROR = 'ERROR'
        FATAL = 'FATAL'

    level = models.CharField(_('x_log_level'), max_length=5, default=Level.INFO.value)
    content = models.CharField(_('x_log_content'), max_length=1024, blank=True, default='')
    source_content = models.CharField(_('x_log_content'), max_length=2048, blank=True, default='')
    create_time = models.DateTimeField(_('x_create_time'), default=timezone.now)

    class Meta:
        abstract = True


class Status(IntChoice):
    DELETED = NameInt(0, _('x_deleted'))
    NORMAL = NameInt(1, _('x_normal'))


class BaseType(PrimaryResourceModel):
    """
    基础类型基类
    """
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=100, default='')
    status = models.PositiveIntegerField(_('x_status'), choices=Status.choices(), default=Status.NORMAL)

    objects = MManager({'status': Status.DELETED})
    original_objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class DefaultFile(PrimaryResourceModel):
    """
    默认文件
    """
    group = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    seq = models.PositiveIntegerField(default=0)
    local_file = models.CharField(max_length=1024, default='')
    mtime = models.CharField(max_length=100, default='')
    remote_file = RemoteFileField()
