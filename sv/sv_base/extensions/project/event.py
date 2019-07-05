import copy
import enum
import logging

from sv_base.models import Event
from sv_base.utils.base.cache import CacheProduct
from sv_base.utils.base.property import cached_property

logger = logging.getLogger(__name__)


class BaseEventHandler:
    """
    基础事件处理类
    """
    target_event_model = Event
    target_event_model_field = None

    class EventFlag(enum.IntEnum):
        """
        事件结果标志
        """
        ENTER_FAILED = 0
        SUCCESS = 1
        SAVE_FAILED = 2

    def __init__(self, target, enable_cache=True):
        """初始化

        :param target: 事件作用对象
        :param enable_cache: 使能缓存检查
        """
        self.target = target
        self.enable_cache = enable_cache

    def progress(self, event, progress_code=0, progress_desc='', event_status=Event.Status.IN_PROGRESS.value):
        """事件进行中

        :param event: 事件
        :param progress_code: 事件进程码
        :param progress_desc: 事件进程描述
        :param event_status: 事件状态
        """
        if self.acquire_event_lock(event, progress_code, Event.ProgressStatus.IN_PROGRESS.value):
            event_obj = self._save_event(event, event_status, progress_code, Event.ProgressStatus.IN_PROGRESS.value,
                                         progress_desc)
            if event_obj:
                return self.EventFlag.SUCCESS
            else:
                self.release_event_lock(event, progress_code)
                return self.EventFlag.SAVE_FAILED
        else:
            return self.EventFlag.ENTER_FAILED

    def over(self, event, progress_code=0, progress_desc='', event_status=Event.Status.IN_PROGRESS.value):
        """事件结束

        :param event: 事件
        :param event: 事件状态
        :param progress_code: 事件进程码
        :param progress_desc: 事件进程描述
        :param event_status: 事件状态
        """
        if self.acquire_event_lock(event, progress_code, Event.ProgressStatus.OVER.value):
            event_obj = self._save_event(event, event_status, progress_code, Event.ProgressStatus.OVER.value,
                                         progress_desc)
            if event_obj:
                if self.enable_cache:
                    self.cache.reset()
                return self.EventFlag.SUCCESS
            else:
                self.release_event_lock(event, progress_code)
                return self.EventFlag.SAVE_FAILED
        else:
            return self.EventFlag.ENTER_FAILED

    def error(self, event, progress_code=0, progress_desc=''):
        """事件出错

        :param event: 事件
        :param progress_code: 事件进程码
        :param progress_desc: 事件进程描述
        """
        if self.acquire_event_lock(event, progress_code, Event.ProgressStatus.ABNORMAL.value):
            event_obj = self._save_event(event, Event.Status.ABNORMAL.value, progress_code,
                                         Event.ProgressStatus.ABNORMAL.value, progress_desc)
            if event_obj:
                if self.enable_cache:
                    self.cache.reset()
                return self.EventFlag.SUCCESS
            else:
                self.release_event_lock(event, progress_code)
                return self.EventFlag.SAVE_FAILED
        else:
            return self.EventFlag.ENTER_FAILED

    @cached_property
    def cache(self):
        """缓存实例

        :return: 缓存实例
        """
        cls = self.__class__
        cache_name = f'{cls.__module__}.{cls.__qualname__}:{self.target.pk}'
        return CacheProduct(cache_name)

    @cached_property
    def event_key(self):
        """事件键

        :return: 事件键 目标主键
        """
        return f'{self.target.pk}'

    def _get_event_create_params(self, event, status, progress_code, progress_status, progress_desc=''):
        """获取事件创建参数

        :param event: 事件
        :param status: 事件状态
        :param progress_code: 进程码
        :param progress_status: 进程状态
        :param progress_desc: 进程描述
        :return: 创建参数
        """
        create_params = {
            self.target_event_model_field: self.target,
            'event': event,
            'status': status,
            'progress_code': progress_code,
            'progress_status': progress_status,
            'progress_desc': progress_desc,
        }
        return create_params

    def _save_event(self, event, status, progress_code, progress_status, progress_desc=''):
        """保存事件

        :param event: 事件
        :param status: 事件状态
        :param progress_code: 进程码
        :param progress_status: 进程状态
        :param progress_desc: 进程描述
        :return: 事件对象
        """
        create_params = self._get_event_create_params(event, status, progress_code, progress_status, progress_desc)
        try:
            event_obj = self.target_event_model.objects.create(**create_params)
        except Exception as e:
            logger.error('save event with params[%s] error: %s', create_params, e)
            event_obj = None
        else:
            if self.enable_cache:
                event_data = copy.copy(event_obj.__dict__)
                event_data.pop('_state', None)
                try:
                    self.cache.set(self.event_key, event_data, None)
                except Exception as e:
                    logger.error('set cache event error: %s', e)

        return event_obj

    def get_event_lock_key(self, event, progress_code, progress_status):
        """事件锁键

        :param event: 事件
        :param progress_code: 事件进程
        :param progress_status: 事件状态
        :return: 事件锁键
        """
        return f'{self.target.pk}_{event}_{progress_code}_{progress_status}'

    def acquire_event_lock(self, event, progress_code, progress_status):
        """获取事件锁

        :param event: 事件
        :param progress_code: 事件进程码
        :param progress_status: 事件状态
        :return: bool
        """
        if self.enable_cache:
            event_lock_key = self.get_event_lock_key(event, progress_code, progress_status)
            try:
                result = self.cache.add(event_lock_key, 1, None)
            except Exception as e:
                logger.error('acquire event lock error: %s', e)
                result = True
        else:
            result = True

        return result

    def release_event_lock(self, event, progress_code, progress_status):
        """释放事件锁

        :param event: 事件
        :param progress_code: 事件进程码
        :param progress_status: 事件状态
        :return: bool
        """
        if self.enable_cache:
            event_lock_key = self.get_event_lock_key(event, progress_code, progress_status)
            try:
                self.cache.delete(event_lock_key)
            except Exception as e:
                logger.error('release event lock error: %s', e)

    def get_current_event_obj(self):
        """获取当前事件对象

        :return: 当前事件对象
        """
        if self.enable_cache:
            try:
                event_data = self.cache.get(self.event_key)
            except Exception as e:
                logger.error('get event from cache error: %s', e)
                event_obj = None
            else:
                event_obj = self.target_event_model().__dict__.update(event_data)
        else:
            event_obj = None

        if event_obj is None:
            filter_params = {
                self.target_event_model_field: self.target,
            }
            event_obj = self.target_event_model.objects.filter(**filter_params).order_by('-create_time').first()

        return event_obj

    def get_latest_start_event_obj(self):
        filter_params = {
            self.target_event_model_field: self.target,
            'event': Event.Status.START.value,
        }
        event_obj = self.target_event_model.objects.filter(**filter_params).order_by('-create_time').first()
        return event_obj


def base_execute(func, args=None, kwargs=None, skip=None, begin=None, end=None, failed=None, sync=True,
                 check=None):
    args = args or ()
    kwargs = kwargs or {}

    flag = check() if check else True
    if not flag:
        if skip:
            skip(*args, **kwargs)
        return False

    if not sync:
        kwargs.update({
            '_end': end,
            '_failed': failed,
        })

    if begin and begin(*args, **kwargs) is False:
        return False

    try:
        func(*args, **kwargs)
    except Exception as e:
        failed(e)

    if sync:
        end()

    return True


def _parse_prev_events(event, prev_events):
    if prev_events:
        if not isinstance(prev_events, (tuple, list)):
            prev_events = [prev_events]
    else:
        prev_events = []

    prev_events.append({
        'event': event,
        'status': (Event.Status.ABNORMAL,),
    })

    events = []
    for prev_event in prev_events:
        if isinstance(prev_event, dict):
            prev_status = prev_event.get('status')
            if prev_status and not isinstance(prev_status, (tuple, list)):
                prev_status = (prev_status,)
            else:
                prev_status = (Event.Status.OVER,)
            prev_event['status'] = prev_status
        else:
            prev_event = {
                'event': prev_event,
                'status': (Event.Status.OVER,),
            }
        events.append(prev_event)

    return events


def _check_events(event, latest_event, latest_event_status, prev_events=None):
    prev_events = _parse_prev_events(event, prev_events)
    flag = False
    for prev_event in prev_events:
        if latest_event == prev_event['event'] and latest_event_status in prev_event['status']:
            flag = True
            break

    return flag


def execute_event(event, latest_event, latest_event_status, func, args=None, kwargs=None,
                  prev_events=None, skip=None, begin=None, end=None, failed=None, sync=True, ignore_check=False):
    """执行事件

    :param event: 准备执行的事件
    :param latest_event: 当前最新的事件
    :param latest_event_status: 当前最新的事件状态
    :param func: 事件函数
    :param args: 事件函数参数
    :param kwargs: 事件函数参数
    :param prev_events: 可接承的事件集(这些事件中任何一个能进入准备执行的事件)
    :param skip: 跳过回调
    :param begin: 开始回调
    :param end: 结束回调
    :param failed: 失败回调
    :param sync: 是否同步
    :param ignore_check: 是否忽略检查
    """
    if ignore_check:
        check = None
    else:
        def check():
            return _check_events(event, latest_event, latest_event_status, prev_events)

    return base_execute(func, args=args, kwargs=kwargs, skip=skip, begin=begin, end=end, failed=failed, sync=sync,
                        check=check)


def _check_event_progress(event, latest_event, latest_event_status, progress_code, latest_progress_code,
                          latest_progress_status):
    flag = False
    if event == latest_event and latest_event_status != Event.Status.OVER:
        if progress_code == latest_progress_code:
            if latest_progress_status == Event.ProgressStatus.ABNORMAL:
                flag = True
        else:
            if latest_progress_status == Event.ProgressStatus.OVER:
                flag = True

    return flag


def execute_event_progress(event, latest_event, latest_event_status, progress_code, latest_progress_code,
                           latest_progress_status, func, args=None, kwargs=None,
                           skip=None, begin=None, end=None, failed=None, sync=True, ignore_check=False):
    if ignore_check:
        check = None
    else:
        def check():
            return _check_event_progress(event, latest_event, latest_event_status, progress_code, latest_progress_code,
                                         latest_progress_status)

    return base_execute(func, args=args, kwargs=kwargs, skip=skip, begin=begin, end=end, failed=failed, sync=sync,
                        check=check)
