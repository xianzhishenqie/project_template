import copy
import enum
import json
import logging

from sv_base.models import Event
from sv_base.extensions.db.common import get_obj
from sv_base.extensions.project.trans import Trans
from sv_base.utils.base.cache import CacheProduct
from sv_base.utils.base.property import cached_property

logger = logging.getLogger(__name__)


class BaseEventHandler:
    """
    基础事件处理类
    """
    target_event_model = Event
    target_event_model_field = None
    target_model = None
    enable_cache = True
    to_db = True

    class EventFlag(enum.IntEnum):
        """
        事件结果标志
        """
        ENTER_FAILED = 0
        SUCCESS = 1
        SAVE_FAILED = 2

    def __init__(self, target, enable_cache=None, to_db=None):
        """初始化

        :param target: 事件作用对象
        :param enable_cache: 使能缓存检查
        :param to_db: 是否保存到数据库
        """
        self.target_model = (self.target_model if self.target_model
                             else getattr(self.target_event_model, self.target_event_model_field).field.related_model)
        target = get_obj(target, self.target_model)
        self.target = target
        if enable_cache is not None:
            self.enable_cache = enable_cache
        if to_db is not None:
            self.to_db = to_db

    @classmethod
    def dump_source_content(cls, content):
        """获取内容的Trans源信息

        :param content: 内容对象 Trans对象
        :return: 内容的Trans源信息
        """
        source_content = content.serialize()
        return json.dumps(source_content)

    @classmethod
    def load_source_content(cls, source_content):
        """载入内容的Trans源信息

        :param source_content: 内容的Trans源信息
        :return: 内容的Trans对象
        """
        if not source_content:
            return source_content

        try:
            content = json.loads(source_content)
            trans = Trans.deserialize(content)
        except Exception as e:
            logger.warning(f'load event source_content error: {e}')
            trans = source_content

        return trans

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
                self.release_event_lock(event, progress_code, Event.ProgressStatus.IN_PROGRESS.value)
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
                self.release_event_lock(event, progress_code, Event.ProgressStatus.OVER.value)
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
                self.release_event_lock(event, progress_code, Event.ProgressStatus.ABNORMAL.value)
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
        return f'event:{self.target_model.__name__}_{self.target.pk}'

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
            'event': event,
            'status': status,
            'progress_code': progress_code,
            'progress_status': progress_status,
            'progress_desc': progress_desc.message if isinstance(progress_desc, Trans) else progress_desc,
            'source_progress_desc': self.dump_source_content(progress_desc) if isinstance(progress_desc,
                                                                                          Trans) else progress_desc,
        }
        if self.target_event_model_field:
            create_params.update({
                self.target_event_model_field: self.target,
            })

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
        event_obj = self.target_event_model(**create_params)
        if self.to_db:
            try:
                event_obj.save()
            except Exception as e:
                logger.error('save event with params[%s] error: %s', create_params, e)
                event_obj = None

        if self.enable_cache and event_obj:
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
        return f'{self.event_key}:{event}_{progress_code}_{progress_status}'

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
        event_obj = None
        if self.enable_cache:
            try:
                event_data = self.cache.get(self.event_key)
            except Exception as e:
                logger.error('get event from cache error: %s', e)
                event_obj = None
            else:
                if event_data:
                    event_obj = self.target_event_model()
                    event_obj.__dict__.update(event_data)

        if event_obj is None and self.to_db:
            filter_params = {}
            if self.target_event_model_field:
                filter_params.update({
                    self.target_event_model_field: self.target,
                })
            event_obj = self.target_event_model.objects.filter(**filter_params).order_by('-create_time').first()

        return event_obj

    def get_latest_start_event_obj(self):
        if self.to_db:
            filter_params = {
                'event': Event.Status.START.value,
            }
            if self.target_event_model_field:
                filter_params.update({
                    self.target_event_model_field: self.target,
                })
            event_obj = self.target_event_model.objects.filter(**filter_params).order_by('-create_time').first()
        else:
            event_obj = None

        return event_obj

    def get_event_progress_desc(self, event):
        if event:
            desc = self.load_source_content(event.source_progress_desc)
            if isinstance(desc, Trans):
                desc = desc.message
        else:
            desc = None

        return desc


def base_execute(func, args=None, kwargs=None, skip=None, begin=None, end=None, failed=None, sync=True,
                 check=None):
    """
    基础事件执行， 如果需要检查(check)并且检查失败, 则退出不执行
    :param func: 事件函数
    :param args: 事件函数参数
    :param kwargs: 事件函数参数
    :param skip: 跳过回调
    :param begin: 开始回调
    :param end: 结束回调
    :param failed: 失败回调
    :param sync: 是否同步
    :param check: check是否正常函数函数
    :return: 是否执行事件
    """
    args = args or ()
    kwargs = kwargs or {}

    # 是否需要检查正确性
    flag = check() if check else True
    if not flag:
        if skip:
            skip()
        return False

    # 异步是更新_end和_failed回调函数
    if not sync:
        kwargs.update({
            '_end': end,
            '_failed': failed,
        })

    if begin and begin() is False:
        return False

    try:
        # 真正执行函数
        func(*args, **kwargs)
    except Exception as e:
        # 失败回调
        failed(e)
        return False

    if sync:
        # 同步时, 结束回调
        end()

    return True


def parse_prev_events(event, prev_events):
    if prev_events:
        if isinstance(prev_events, (tuple, list)):
            prev_events = list(prev_events)
        else:
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
            if prev_status:
                if not isinstance(prev_status, (tuple, list)):
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


def check_events(event, latest_event, latest_event_status, prev_events):
    """
    检查事件的正确性, 不正确不能继续执行事件
    :param event: 检查的事件
    :param latest_event: 最新的事件
    :param latest_event_status: 最新的事件状态
    :param prev_events: 可接受的事件集合
    :return: 事件是否正确，True 正确， False 不正确
    """
    flag = False
    for prev_event in prev_events:

        # 判断当前事件，和当前事件状态是否在可接受的范围内
        if latest_event == prev_event['event'] and latest_event_status in prev_event['status']:
            flag = True
            break

    return flag


def execute_event(event, latest_event, latest_event_status, prev_events, func, args=None, kwargs=None,
                  skip=None, begin=None, end=None, failed=None, sync=True, ignore_check=False):
    """
    执行事件

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
            return check_events(event, latest_event, latest_event_status, prev_events)

    return base_execute(func,
                        args=args,
                        kwargs=kwargs,
                        skip=skip,
                        begin=begin,
                        end=end,
                        failed=failed,
                        sync=sync,
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
