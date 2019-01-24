from django.http import QueryDict
from django.utils import six
from sv_base.utils.common.ulist import listfilter, valuefilter


class DataFilter:

    def __init__(self, data, strict=False):
        self.data = data
        self.strict = strict
        self._is_query_dict = isinstance(data, QueryDict)

    def get(self, field_name, filter_param=str):
        data = self.data.get(field_name)
        if filter_param is bool:
            if data is None:
                return data
            else:
                data = handle_bool_value(data)
        return valuefilter(data, filter_param, strict=self.strict)

    def getlist(self, field_name, filter_param=str):
        data = self.data.getlist(field_name) if self._is_query_dict else self.data.get(field_name)
        if not isinstance(data, (list, tuple, set)):
            data = [data]
        if filter_param is bool:
            data = [handle_bool_value(item) for item in data]
        return listfilter(data, filter_param, strict=self.strict) if data else []


class RequestData:

    def __init__(self, request, is_query=False, data_filter_class=DataFilter, strict=False):
        self.request = request
        if is_query:
            self.data = request.query_params if hasattr(request, 'query_params') else getattr(request, 'GET', {})
        else:
            self.data = request.data if hasattr(request, 'data') else request.POST
        self.data_filter = data_filter_class(self.data, strict)

    def get(self, field_name, filter_param=str):
        return self.data_filter.get(field_name, filter_param)

    def getlist(self, field_name, filter_param=str):
        return self.data_filter.getlist(field_name, filter_param)

    def remove_field(self, field_name):
        self.data._mutable = True
        del self.data[field_name]
        self.data._mutable = False


def handle_bool_value(value):
    if isinstance(value, six.string_types):
        if value == 'true':
            return True
        elif value == 'false':
            return False

        try:
            return bool(int(value))
        except:
            pass

    return value
