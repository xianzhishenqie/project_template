import pickle

from django.db import models
from django.utils import timezone


class Executor(models.Model):
    """
    序列化执行任务 func执行函数  params执行参数 context执行上下文
    """
    func = models.TextField(default='')
    params = models.TextField(default='')
    context = models.TextField(default='')

    create_time = models.DateTimeField(default=timezone.now)

    @classmethod
    def add_executor(cls, executor):
        condition = cls.dump_executor(executor)
        return cls.objects.create(**condition)

    @classmethod
    def dump_executor(cls, executor):
        condition = {
            'func': pickle.dumps(executor['func']),
            'params': pickle.dumps(executor.get('params', {})),
        }
        return condition

    def load_executor(self):
        executor = {
            'func': pickle.loads(str(self.func)),
            'params': pickle.loads(str(self.params)),
        }
        return executor

    def execute(self, *args, **kwargs):
        executor = self.load_executor()
        func = executor['func']
        params = executor['params']
        params.update(kwargs)
        return func(*args, **params)
