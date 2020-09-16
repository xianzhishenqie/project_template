from sv_base.utils.base.thread import Shared


class LanguageShared(Shared):
    key = 'language'

    @classmethod
    def _get_shared(cls):
        from django.utils import translation
        return translation.get_language()

    @classmethod
    def _set_shared(cls, data):
        from django.utils import translation
        translation.activate(data)


class RpcContextShared(Shared):
    key = 'rpc_ctx'

    @classmethod
    def _get_shared(cls):
        from sv_base.extensions.service.rpc import get_context
        return get_context()

    @classmethod
    def _set_shared(cls, data):
        from sv_base.extensions.service.rpc import set_context
        set_context(data)
