import pickle

from django.db import models
from django.utils import timezone

from sv_base.utils.base.text import ec


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
