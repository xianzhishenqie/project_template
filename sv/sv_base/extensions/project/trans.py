import copy

from django.utils.translation import gettext, ngettext, npgettext, ngettext_lazy, npgettext_lazy

from sv_base.utils.base.property import cached_property


class Trans:
    """
    国际化字符串类
    """
    code = None
    params = None

    def __init__(self, *gettext_args, gettext_func=None, code=None):
        """生成初始化实例对象

        :param gettext_args: 国际化字符串
        :param gettext_func: 国际化字符串方法
        :param code: 国际化字符串标识码
        :return: 实例对象
        """
        if not gettext_args:
            raise Exception('Trans gettext_args cannot be empty')

        # 标识码
        self.code = code
        # 国际化字符串
        gettext_args = list(gettext_args)
        gettext_args_len = len(gettext_args)
        if gettext_func is None:
            if gettext_args_len == 1:
                gettext_func = gettext
            elif gettext_args_len == 2:
                gettext_func = ngettext
            elif gettext_args_len == 3:
                gettext_func = npgettext
            else:
                gettext_func = npgettext
                gettext_args = gettext_args[0: 3]

        self.gettext_args = gettext_args
        self.gettext_func = gettext_func

    def __call__(self, _number_key=None, **kwargs):
        """载入格式化参数
        :param _number_key: 格式化参数中代表数量的参数
        :param kwargs: 格式化参数
        :return: 带参数的新Trans对象
        """
        new_instance = copy.deepcopy(self)
        del new_instance.message
        if new_instance.gettext_func in (ngettext, npgettext, ngettext_lazy, npgettext_lazy):
            number_key = _number_key or list(kwargs.keys())[0]
            new_instance.gettext_args.append(kwargs[number_key])

        new_instance.params = kwargs

        return new_instance

    def __str__(self):
        return self.message

    def get_message(self):
        """获取翻译结果

        :return: 翻译结果
        """
        message = self.gettext_func(*self.gettext_args)
        if self.params:
            message = message % self.params
        return message

    @cached_property
    def message(self):
        """缓存翻译结果

        :return: 翻译结果
        """
        return self.get_message()
