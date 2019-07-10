import enum
import logging


logger = logging.getLogger(__name__)


class TaskStatus(enum.IntEnum):
    WAIT = 0
    PROGRESS = 1
    OVER = 2


class Task:

    def __init__(self, func, args=None, kwargs=None):
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or ()
        self.status = TaskStatus.WAIT

    def execute(self):
        self.status = TaskStatus.PROGRESS
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            logger.error('execute task[%s(args=%s, kwargs=%s)] error: %s', self.func, self.args, self.kwargs, e)
        self.status = TaskStatus.OVER


class SyncTaskPool:

    def __init__(self):
        self.tasks = []

    def add(self, func, args=None, kwargs=None):
        task = Task(func, args=args, kwargs=kwargs)
        self.tasks.append(task)
        self.run()

    def run(self):
        if not self.tasks:
            return

        if self.tasks[0].status == TaskStatus.WAIT:
            self.tasks[0].execute()
            self.tasks.pop(0)
            if self.tasks:
                self.run()
