from nameko.extensions import DependencyProvider


class ContextData(DependencyProvider):

    def get_dependency(self, worker_ctx):
        return worker_ctx.data
