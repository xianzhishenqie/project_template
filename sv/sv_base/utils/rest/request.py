from typing import Union, Type

from django.http import QueryDict
from rest_framework.request import Request

from sv_base.utils.common.ulist import list_filter, value_filter


class DataFilter:
    """
    请求数据过滤器
    """
    def __init__(self, data: Union[QueryDict, dict], strict: bool = False) -> None:
        """初始化

        :param data: 请求数据
        :param strict: 严格模式
        """
        self.data = data
        self.strict = strict
        self._is_query_dict = isinstance(data, QueryDict)

    def get(self, field_name: str, filter_param: type = str) -> object:
        """获取有效字段值

        :param field_name: 字段名称
        :param filter_param: 过滤参数
        :return: 字段值
        """
        data = self.data.get(field_name)
        if filter_param is bool:
            if data is None:
                return data
            else:
                data = handle_bool_value(data)
        return value_filter(data, filter_param, strict=self.strict)

    def getlist(self, field_name: str, filter_param: type = str) -> object:
        """获取有效字段值

        :param field_name: 字段名称
        :param filter_param: 过滤参数
        :return: 字段值
        """
        data = self.data.getlist(field_name) if self._is_query_dict else self.data.get(field_name)
        if not isinstance(data, (list, tuple, set)):
            data = [data]
        if filter_param is bool:
            data = [handle_bool_value(item) for item in data]
        return list_filter(data, filter_param, strict=self.strict) if data else []


class RequestData:
    """
    请求数据封装类
    """
    def __init__(self, request: Union[Request], is_query: bool = False, data_filter_class: Type[DataFilter] = DataFilter, strict: bool = False) -> None:
        """请求数据初始化

        :param request: 请求对象
        :param is_query: 是否查询数据
        :param data_filter_class: 数据过滤处理类
        :param strict: 严格模式
        """
        self.request = request
        if is_query:
            self.data = request.query_params if hasattr(request, 'query_params') else getattr(request, 'GET', {})
        else:
            self.data = request.data if hasattr(request, 'data') else request.POST
        self.data_filter = data_filter_class(self.data, strict)

    def get(self, field_name: str, filter_param: type = str) -> object:
        """获取有效字段值

        :param field_name: 字段名称
        :param filter_param: 过滤参数
        :return: 字段值
        """
        return self.data_filter.get(field_name, filter_param)

    def getlist(self, field_name: str, filter_param: type = str) -> object:
        """获取有效字段值

        :param field_name: 字段名称
        :param filter_param: 过滤参数
        :return: 字段值
        """
        return self.data_filter.getlist(field_name, filter_param)

    def remove_field(self, field_name: str) -> None:
        """移除请求数据字段

        :param field_name: 字段名
        """
        self.data._mutable = True
        del self.data[field_name]
        self.data._mutable = False


def handle_bool_value(value: object) -> object:
    """处理bool类型的请求值

    :param value: 请求值
    :return: 返回值
    """
    if isinstance(value, str):
        if value == 'true':
            return True
        elif value == 'false':
            return False

        try:
            return bool(int(value))
        except:
            pass

    return value
