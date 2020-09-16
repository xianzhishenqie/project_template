import time

from sv_base.extensions.service.base import ServiceBase
from sv_base.extensions.service.rpc import rpc


class ServiceTest(ServiceBase):
    name = 'sv_test'

    @rpc
    def test(self, sleep=None):
        if sleep:
            time.sleep(sleep)

        return sleep
