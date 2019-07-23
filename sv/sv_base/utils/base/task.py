import copy
import enum
import logging

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

    def run(self, over_callback=None):
        wait_tasks = [task for task in self.tasks if task.status == TaskStatus.WAIT]
        errors = []

        if wait_tasks:
            for task in copy.copy(wait_tasks):

                def tmp(task=task):
                    task.execute()
                    if task.e:
                        errors.append(task.e)
                    wait_tasks.pop(wait_tasks.index(task))

                    if not wait_tasks and over_callback:
                        over_callback(errors)

                async_exe(tmp)
                self.tasks.pop(self.tasks.index(task))
        else:
            if over_callback:
                over_callback(errors)
