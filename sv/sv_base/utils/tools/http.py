from functools import partial
from requests import Session

from django.utils import six


DEFAULT_TIMEOUT_SECONDS = 60


class HttpClient(Session):
    """
    http客户端
    """
    def __init__(self, base_url=None, timeout=DEFAULT_TIMEOUT_SECONDS):
        """初始化http客户端实例

        :param base_url: 基础url
        :param timeout: 超时时间
        """
        super(HttpClient, self).__init__()

        self.base_url = base_url or ''
        self.timeout = timeout

    def mpost(self, url, kwargs):
        """post请求

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.post(url, **self._set_request_timeout(kwargs))

    def mget(self, url, kwargs):
        """get请求

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.get(url, **self._set_request_timeout(kwargs))

    def mdelete(self, url, kwargs):
        """delete请求

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.delete(url, **self._set_request_timeout(kwargs))

    def _set_request_timeout(self, kwargs):
        """如果未设置超时时间设置默认的超时时间

        :param kwargs: 请求参数
        :return: 请求参数
        """
        kwargs.setdefault('timeout', self.timeout)
        return kwargs

    def murl(self, pathfmt, *args):
        """格式化url

        :param pathfmt: 格式化url模板
        :param args: url参数
        :return: url
        """
        for arg in args:
            if not isinstance(arg, str):
                raise ValueError(
                    'Expected a string but found {0} ({1}) '
                    'instead'.format(arg, type(arg))
                )

        quote_f = partial(six.moves.urllib.parse.quote_plus, safe="/:")
        args = map(quote_f, args)

        return self.base_url + pathfmt.format(*args)

    @staticmethod
    def result(response, json=False, binary=False):
        """处理响应返回结果

        :param response: 响应
        :param json: 返回json
        :param binary: 返回binary
        :return: 返回结果
        """
        assert not (json and binary)

        if json:
            return response.json()
        if binary:
            return response.content

    def jget(self, url, **kwargs):
        """get请求json

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.result(self.mget(url, **kwargs), json=True)

    def jpost(self, url, **kwargs):
        """post请求json

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.result(self.mpost(url, **kwargs), json=True)

    def jdelete(self, url, **kwargs):
        """delete请求json

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.result(self.mdelete(url, **kwargs), json=True)
