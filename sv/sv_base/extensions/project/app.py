import os

from importlib import import_module

from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings, LazySettings, Settings
from django.conf.urls import url
from django.urls import include, path
from channels.routing import URLRouter

from sv_base.utils.base.thread import async_exe, async_exe_once
from sv_base.extensions.rest.routers import rest_path
from sv_base.extensions.websocket.routers import ws_path


def get_app_name(module_name):
    """获取模块所在app名称。

    :param module_name: 模块名称
    :return: app名称
    """
    return module_name.split('.')[0]


def get_service_name(module_name):
    """获取模块所在服务名称。

    :param module_name: 模块名称
    :return: 服务名称
    """
    return module_name.split('.')[1]


def _get_sub_path(path_name):
    """获取子路径。

    :param path_name: 路径名称
    :return: 子路径
    """
    if path_name:
        return '{path_name}/'.format(path_name=path_name)
    else:
        return ''


def get_app_urls(app_name):
    """获取app路由

    :param app_name: app名称
    :return: 子模块对应普通路由, 子模块对应接口路由
    """
    patterns = {}
    apipatterns = {}
    # app路径名称
    app_path_name = settings.SV_APP_PATH[app_name]
    # app路径
    app_path = _get_sub_path(app_path_name)
    # app子模块
    for sub_module_name in settings.SUB_MODULES:
        # 检查收集子模块的路由文件
        urls_name = '{app_name}.{sub_module}.urls'.format(
            app_name=app_name,
            sub_module=sub_module_name,
        )
        try:
            urls_module = import_module(urls_name)
        except ImportError:
            pass
        else:
            urls_module.urlpatterns = getattr(urls_module, 'urlpatterns', [])
            urls_module.apiurlpatterns = getattr(urls_module, 'apiurlpatterns', [])
            if hasattr(urls_module, 'viewsets'):
                # 收集viewsets api路由
                urls_module.apiurlpatterns += rest_path(urls_module.viewsets)

            if urls_module.urlpatterns:
                # 收集普通路由
                patterns.setdefault(sub_module_name, []).append(
                    path(app_path, include((urls_module.urlpatterns, app_name)))
                )

            if urls_module.apiurlpatterns:
                # 收集api路由
                apipatterns.setdefault(sub_module_name, []).append(
                    path(app_path, include((urls_module.apiurlpatterns, app_name)))
                )

    return patterns, apipatterns


def get_sv_urls():
    """获取项目路由。

    :return: 普通路由, 接口路由
    """
    patterns = []
    apipatterns = []

    app_sub_module_patterns = {}
    app_sub_module_apipatterns = {}
    for app_name in settings.SV_APP_NAMES:
        urls_name = '{app_name}.urls'.format(
            app_name=app_name,
        )
        try:
            urls_module = import_module(urls_name)
        except ImportError:
            pass
        else:
            # 收集app根目录的路由
            urls_module.urlpatterns = getattr(urls_module, 'urlpatterns', [])
            urls_module.apiurlpatterns = getattr(urls_module, 'apiurlpatterns', [])
            if hasattr(urls_module, 'viewsets'):
                urls_module.apiurlpatterns += rest_path(urls_module.viewsets)

            path_name = settings.APP_PATH[app_name]
            if urls_module.urlpatterns:
                patterns.append(
                    path(_get_sub_path(path_name), include((urls_module.urlpatterns, app_name)))
                )

            if urls_module.apipatterns:
                apipatterns.append(
                    path(_get_sub_path(path_name), include((urls_module.apiurlpatterns, app_name)))
                )
        # 收集app子模块的路由
        app_patterns, app_apipatterns = get_app_urls(app_name)
        app_sub_module_patterns[app_name] = app_patterns
        app_sub_module_apipatterns[app_name] = app_apipatterns

    # 收集子模块的普通路由
    for app_name, app_patterns in app_sub_module_patterns.items():
        for sub_module_name, sub_module_patterns in app_patterns.items():
            sub_module_path_name = settings.SUB_MODULES[sub_module_name]
            patterns.append(
                path(_get_sub_path(sub_module_path_name),
                     include((sub_module_patterns, app_name), namespace=sub_module_name))
            )

    # 收集子模块的api路由
    for app_name, app_apipatterns in app_sub_module_apipatterns.items():
        for sub_module_name, sub_module_apipatterns in app_apipatterns.items():
            sub_module_path_name = settings.SUB_MODULES[sub_module_name]
            apipatterns.append(
                path(_get_sub_path(sub_module_path_name),
                     include((sub_module_apipatterns, app_name), namespace=sub_module_name))
            )

    return patterns, apipatterns


def _get_sub_channel_pattern(path_name):
    """获取channel子路径。

    :param path_name: 路径名称
    :return: 子路径
    """
    if path_name:
        return r'^{path_name}/'.format(path_name=path_name)
    else:
        return ''


def get_app_routers(app_name):
    """获取app channels路由

    :param app_name: app名称
    :return: 子模块对应路由
    """
    patterns = {}
    app_path_name = settings.SV_APP_PATH[app_name]

    for sub_module_name in settings.SUB_MODULES:
        # 检查收集子模块的路由文件
        routers_name = '{app_name}.{sub_module}.routing'.format(
            app_name=app_name,
            sub_module=sub_module_name,
        )
        try:
            routers_module = import_module(routers_name)
        except ImportError:
            pass
        else:
            routers_module.routerpatterns = getattr(routers_module, 'routerpatterns', [])
            if hasattr(routers_module, 'websockets'):
                routers_module.routerpatterns.extend(ws_path(routers_module.websockets))

            # 收集路由
            patterns.setdefault(sub_module_name, []).append(
                url(_get_sub_channel_pattern(app_path_name), URLRouter(routers_module.routerpatterns))
            )

    return patterns


def get_sv_routers():
    """获取项目channels路由。

    :return: 项目channels路由列表
    """
    patterns = []

    app_sub_module_patterns = {}
    for app_name in settings.SV_APP_NAMES:
        # 检查收集app根目录的路由
        routers_name = '{app_name}.routers'.format(
            app_name=app_name,
        )
        try:
            routers_module = import_module(routers_name)
        except ImportError:
            pass
        else:
            routers_module.routerpatterns = getattr(routers_module, 'routerpatterns', [])
            if hasattr(routers_module, 'websockets'):
                routers_module.routerpatterns.append(ws_path(routers_module.websockets))

            path_name = settings.APP_PATH[app_name]
            patterns.append(
                url(_get_sub_channel_pattern(path_name), URLRouter(routers_module.routerpatterns))
            )

        app_sub_module_patterns[app_name] = get_app_routers(app_name)

    # 收集子模块的路由
    for app_name, app_patterns in app_sub_module_patterns.items():
        for sub_module_name, sub_module_patterns in app_patterns.items():
            sub_module_path_name = settings.SUB_MODULES[sub_module_name]
            patterns.append(
                url(_get_sub_channel_pattern(sub_module_path_name), URLRouter(sub_module_patterns))
            )

    return patterns


def sync_init(app_name):
    """app初始化

    :param app_name: app名称
    """
    app_module = import_module(app_name)
    if hasattr(app_module, 'sync_init'):
        # 同步初始化
        app_module.sync_init()
    if hasattr(app_module, 'async_init'):
        # 异步初始化
        async_exe(app_module.async_init)
    if hasattr(app_module, 'async_global_init'):
        # 异步全局初始化(进程无关的初始化)
        async_exe_once(app_module.async_global_init)

    # 初始化资源模块
    resource_name = '{app_name}.resources'.format(
        app_name=app_name,
    )
    resource_path = os.path.join(settings.BASE_DIR, resource_name.replace('.', '/') + '.py')
    if os.path.exists(resource_path):
        import_module(resource_name)

    # 初始化验证
    validator_name = '{app_name}.validators'.format(
        app_name=app_name,
    )
    validator_path = os.path.join(settings.BASE_DIR, validator_name.replace('.', '/') + '.py')
    if os.path.exists(validator_path):
        import_module(validator_name)


class AppConfig(DjangoAppConfig):
    """
    继承django的AppConfig，添加自定义的app初始化功能。
    """
    def ready(self):
        """app载入时执行。

        """
        sync_init(self.name)


class LazyAppSettings(LazySettings):
    """
    继承django的LazySettings，添加自定义的app配置功能。
    """

    _app_name = None

    def __init__(self, app_name):
        self._app_name = app_name
        super(LazyAppSettings, self).__init__()

    def _setup(self, name=None):
        self._wrapped = AppSettings(self._app_name)

    def __setattr__(self, name, value):
        if name == '_app_name':
            self.__dict__['_app_name'] = value
        else:
            if name == '_wrapped':
                _app_name = self.__dict__.pop('_app_name', None)
                self.__dict__.clear()
                self.__dict__['_app_name'] = _app_name
            else:
                self.__dict__.pop(name, None)
            super(LazySettings, self).__setattr__(name, value)


class AppSettings(Settings):
    """
    继承django的LazySettings，添加自定义的app配置初始化功能。
    """

    def __init__(self, app_name):
        # 载入默认的app配置
        app_settings_module = '{app_name}.setting'.format(
            app_name=app_name,
        )
        default_app_settings = import_module(app_settings_module)
        for setting in dir(default_app_settings):
            if setting.isupper():
                setattr(self, setting, getattr(default_app_settings, setting))

        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = app_settings_module

        # 载入覆盖的app配置
        self._explicit_settings = set()
        config_settings = settings.APP_SETTINGS.get(app_name)
        if config_settings:
            for setting, setting_value in config_settings.items():
                if isinstance(setting_value, dict) and hasattr(self, setting):
                    getattr(self, setting).update(setting_value)
                else:
                    setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

        # 载入关联计算的app配置
        if hasattr(default_app_settings, 'load_related'):
            default_app_settings.load_related(self)


def load_app_settings(package):
    """载入app配置。

    :param package: 包名称
    :return: app配置
    """
    app_name = get_app_name(package)
    app_settings = LazyAppSettings(app_name)
    settings.MS[app_name] = app_settings
    return app_settings
