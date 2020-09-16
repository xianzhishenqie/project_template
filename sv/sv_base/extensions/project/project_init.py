
def init():
    """
    项目初始化加载
    :return: 无
    """
    register_thread_shared()


def register_thread_shared():
    """
    注册线程共享变量
    :return: 无
    """
    from sv_base.utils.base.thread import register_shared
    from sv_base.extensions.project import thread_shared

    register_shared((
        thread_shared.LanguageShared,
        thread_shared.RpcContextShared,
    ))
