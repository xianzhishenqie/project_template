from functools import partial
from requests import Session
from requests.models import Response
from typing import Optional, Union

from django.utils import six


DEFAULT_TIMEOUT_SECONDS = 60


class HttpClient(Session):
    """
    http客户端
    """
    def __init__(self, base_url: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        """初始化http客户端实例

        :param base_url: 基础url
        :param timeout: 超时时间
        """
        super(HttpClient, self).__init__()

        self.base_url = base_url or ''
        self.timeout = timeout

    def mpost(self, url: str, kwargs: dict) -> Response:
        """post请求

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.post(url, **self._set_request_timeout(kwargs))

    def mget(self, url: str, kwargs: dict) -> Response:
        """get请求

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.get(url, **self._set_request_timeout(kwargs))

    def mdelete(self, url: str, kwargs: dict) -> Response:
        """delete请求

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.delete(url, **self._set_request_timeout(kwargs))

    def _set_request_timeout(self, kwargs: dict) -> dict:
        """如果未设置超时时间设置默认的超时时间

        :param kwargs: 请求参数
        :return: 请求参数
        """
        kwargs.setdefault('timeout', self.timeout)
        return kwargs

    def murl(self, pathfmt: str, *args) -> str:
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
    def result(response: Response, json: bool = False, binary: bool = False) -> Union[dict, bytes, None]:
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

    def jget(self, url: str, **kwargs) -> dict:
        """get请求json

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.result(self.mget(url, **kwargs), json=True)

    def jpost(self, url: str, **kwargs) -> dict:
        """post请求json

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.result(self.mpost(url, **kwargs), json=True)

    def jdelete(self, url: str, **kwargs) -> dict:
        """delete请求json

        :param url: 请求url
        :param kwargs: 请求参数
        :return: 请求结果
        """
        return self.result(self.mdelete(url, **kwargs), json=True)
