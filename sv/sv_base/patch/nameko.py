"""
nameko补丁

"""
from nameko.constants import AMQP_URI_CONFIG_KEY, SERIALIZER_CONFIG_KEY, DEFAULT_SERIALIZER, AMQP_SSL_CONFIG_KEY
from nameko.events import EventDispatcher
from nameko.rpc import RpcConsumer, get_rpc_exchange, Responder


def event_dispatcher_get_dependency(self, worker_ctx):
    """ Inject a dispatch method onto the service instance
    """
    extra_headers = self.get_message_headers(worker_ctx)

    def dispatch(event_type, event_data, **kwargs):
        self.publisher.publish(
            event_data,
            exchange=self.exchange,
            routing_key=event_type,
            extra_headers=extra_headers,
            **kwargs,
        )

    return dispatch


_rpc_consumer_handle_result_default = RpcConsumer.handle_result


def rpc_consumer_handle_result(self, message, result, exc_info):
    from sv_base.extensions.service.rpc import RpcResult

    if isinstance(result, RpcResult):
        rpc_result = result
        amqp_uri = self.container.config[AMQP_URI_CONFIG_KEY]
        serializer = self.container.config.get(
            SERIALIZER_CONFIG_KEY, DEFAULT_SERIALIZER
        )
        exchange = get_rpc_exchange(self.container.config)
        ssl = self.container.config.get(AMQP_SSL_CONFIG_KEY)

        responder = Responder(amqp_uri, exchange, serializer, message, ssl=ssl)
        result, exc_info = responder.send_response(rpc_result.result, exc_info)

        self.queue_consumer.ack_message(message)

        if rpc_result.rely_callback:
            rpc_result.rely_callback()

        return result, exc_info
    else:
        return _rpc_consumer_handle_result_default(self, message, result, exc_info)


def monkey_patch():
    """打补丁

    """
    EventDispatcher.get_dependency = event_dispatcher_get_dependency
    RpcConsumer.handle_result = rpc_consumer_handle_result
