import enum
import json
import logging

from sv_base.extensions.db.common import get_obj
from sv_base.extensions.project.trans import Trans
from sv_base.models import Log


logger = logging.getLogger(__name__)


class LoggerException(Exception):
    pass


class Logger:
    """
    基础日志处理类
    """
    logger_level_map = {
        Log.Level.INFO: logging.INFO,
        Log.Level.DEBUG: logging.DEBUG,
        Log.Level.WARNING: logging.WARNING,
        Log.Level.ERROR: logging.ERROR,
        Log.Level.FATAL: logging.FATAL,
    }

    target_log_model = Log
    target_log_model_field = None

    def __init__(self, target):
        target_model = getattr(self.target_log_model, self.target_log_model_field).field.related_model
        target = get_obj(target, target_model)
        self.target = target

    @classmethod
    def dump_source_content(cls, content):
        """获取日志内容的Trans源信息

        :param content: 日志内容对象 Trans对象
        :return: 日志内容的Trans源信息
        """
        source_content = content.serialize()
        return json.dumps(source_content)

    @classmethod
    def load_source_content(cls, source_content):
        """载入日志内容的Trans源信息

        :param source_content: 日志内容的Trans源信息
        :return: 日志内容的Trans对象
        """
        if not source_content:
            return source_content

        try:
            content = json.loads(source_content)
            trans = Trans.deserialize(content)
        except Exception as e:
            logger.warning(f'load logger source_content error: {e}')
            trans = source_content

        return trans

    def info(self, content, to_file=True, to_db=True):
        """info日志

        :param content: 日志内容对象
        :param to_file: 写入文件
        :param to_db: 写入数据库
        :return: 场景日志对象
        """
        return self._log(Log.Level.INFO, content, to_file=to_file, to_db=to_db)

    def debug(self, content, to_file=True, to_db=True):
        """info日志

        :param content: 日志内容对象
        :param to_file: 写入文件
        :param to_db: 写入数据库
        :return: 场景日志对象
        """
        return self._log(Log.Level.DEBUG, content, to_file=to_file, to_db=to_db)

    def warning(self, content, to_file=True, to_db=True):
        """warn日志

        :param content: 日志内容对象
        :param to_file: 写入文件
        :param to_db: 写入数据库
        :return: 场景日志对象
        """
        return self._log(Log.Level.WARNING, content, to_file=to_file, to_db=to_db)

    def error(self, content, to_file=True, to_db=True):
        """error日志

        :param content: 日志内容对象
        :param to_file: 写入文件
        :param to_db: 写入数据库
        :return: 场景日志对象
        """
        return self._log(Log.Level.ERROR, content, to_file=to_file, to_db=to_db)

    def fatal(self, content, to_file=True, to_db=True):
        """fatal日志

        :param content: 日志内容对象
        :param to_file: 写入文件
        :param to_db: 写入数据库
        :return: 场景日志对象
        """
        return self._log(Log.Level.FATAL, content, to_file=to_file, to_db=to_db)

    def _get_log_create_params(self, level, message, source_content):
        """获取事件创建参数

        :param level: 等级
        :param message: 内容
        :param source_content: 源内容
        :return: 创建参数
        """

        create_params = {
            self.target_log_model_field: self.target,
            'level': level,
            'content': message,
            'source_content': source_content,
        }
        return create_params

    def _log(self, level, content, to_file=True, to_db=True):
        """日志

        :param level: 日志等级
        :param content: 日志内容对象
        :param to_file: 写入文件
        :param to_db: 写入数据库
        :return: 日志对象
        """
        if isinstance(content, enum.Enum):
            content = content.value

        if isinstance(content, Trans):
            message = content.message
        else:
            message = content

        if to_file:
            logger.log(self.logger_level_map[level], message)

        log = None
        if to_db:
            create_params = self._get_log_create_params(
                level=level,
                message=message,
                source_content=self.dump_source_content(content) if isinstance(content, Trans) else content,
            )
            try:
                log = self.target_log_model.objects.create(**create_params)
            except Exception as e:
                logger.error('save logger failed: %s', e)

        return log

    def get_log_message(self, log):
        if log:
            log = self.load_source_content(log.source_content)
            if isinstance(log, Trans):
                log = log.message
        else:
            log = None

        return log

    def get_latest_log(self):
        """获取最新日志

        :return: 最新日志对象
        """
        log = self.target_log_model.objects.filter(**{
            self.target_log_model_field: self.target,
        }).order_by('-create_time').first()
        return log

    def get_latest_message(self):
        return self.get_log_message(self.get_latest_log())

    def get_logs(self, level, start_time=None):
        logs = self.target_log_model.objects.filter(**{
            self.target_log_model_field: self.target,
            'level': level,
        })
        if start_time:
            logs = logs.filter(create_time__gte=start_time)
        logs = logs.order_by('-create_time')
        return logs

    def get_error_logs(self, start_time=None):
        return self.get_logs(Log.Level.ERROR, start_time=start_time)

    def get_error_messages(self, start_time=None):
        return [self.get_log_message(log) for log in self.get_error_logs(start_time=start_time)]
