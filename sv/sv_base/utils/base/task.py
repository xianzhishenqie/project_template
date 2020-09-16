import logging

import enum

from sv_base.utils.base.thread import async_exe

logger = logging.getLogger(__name__)


class TaskStatus(enum.IntEnum):
    WAIT = 0
    PROGRESS = 1
    OVER = 2


class Task:

    def __init__(self, func, args=None, kwargs=None):
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.status = TaskStatus.WAIT
        self.e = None

    def execute(self):
        self.status = TaskStatus.PROGRESS
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.e = e
            logger.error('execute task[%s(args=%s, kwargs=%s)] error: %s', self.func, self.args, self.kwargs, e)
        self.status = TaskStatus.OVER


class TaskPool:

    def __init__(self):
        self.tasks = []

    def add(self, func, args=None, kwargs=None):
        task = Task(func, args=args, kwargs=kwargs)
        self.tasks.append(task)


class SyncTaskPool(TaskPool):

    def exe(self, func, args=None, kwargs=None):
        self.add(func, args=args, kwargs=kwargs)
        self.run()

    def run(self):
        if not self.tasks:
            return

        if self.tasks[0].status == TaskStatus.WAIT:
            self.tasks[0].execute()
            self.tasks.pop(0)
            if self.tasks:
                self.run()


class AsyncTaskPool(TaskPool):

    def __init__(self, pool_size=None):
        super().__init__()
        self.pool_size = pool_size
        self.progress_tasks = []
        self.running = False

    def run(self, over_callback=None):
        if self.running:
            return

        errors = []
        if not self.tasks:
            if over_callback:
                over_callback(errors)
            return

        self.running = True
        pool_size = self.pool_size if self.pool_size else len(self.tasks)
        for i in range(pool_size):
            async_exe(self._one_queue, (errors, over_callback))

    def _next_task(self):
        task = self.tasks.pop(0) if self.tasks else None
        return task

    def _one_queue(self, errors, over_callback):
        while self.tasks:
            task = self._next_task()
            self.progress_tasks.append(task)
            task.execute()
            if task.e:
                errors.append(task.e)
            self.progress_tasks.remove(task)

        if self.running and not self.progress_tasks:
            self.running = False
            if over_callback:
                over_callback(errors)
