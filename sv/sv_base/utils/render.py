import copy

from typing import Optional

from django.http.request import HttpRequest
from django.shortcuts import render


class AppRender:
    """
    app 渲染模板，用于app子模块的模板路由
    """
    def __init__(self, module: str, template_path: Optional[str] = None) -> None:
        """初始化渲染器

        :param module: 所在模块
        :param template_path: 模板路径
        """
        self.path_parts = module.split('.')
        if template_path:
            self.path_parts.append(template_path)

    def render(self,
               request: HttpRequest,
               template_name: str,
               context: Optional[dict] = None,
               content_type: Optional[str] = None,
               status: Optional[int] = None,
               using: Optional[str] = None) -> object:
        """重载渲染方法，寻找自定义模板路径

        :param request: 请求对象
        :param template_name: 模板名称
        :param context: 模板上下文
        :param content_type: http内容类型
        :param status: http状态
        :param using: 模板引擎
        :return: http响应对象
        """
        path_parts = copy.copy(self.path_parts)
        path_parts.append(template_name)
        template_name = '/'.join(path_parts)

        return render(request, template_name, context, content_type, status, using)


def get_app_render(module: str, template_path: Optional[str] = None) -> function:
    """获取app对应的渲染方法

    :param module: 模块名称
    :param template_path: 模板路径
    :return: app渲染方法
    """
    return AppRender(module, template_path).render
