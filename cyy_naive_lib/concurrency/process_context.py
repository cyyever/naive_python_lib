import multiprocessing
import multiprocessing.connection
import multiprocessing.context
import multiprocessing.managers
import multiprocessing.synchronize

from .context import ConcurrencyContext


class ProcessContext(ConcurrencyContext):
    def __init__(self, ctx: multiprocessing.context.BaseContext | None = None) -> None:
        if ctx is None:
            ctx = multiprocessing
        if hasattr(ctx, "get_context"):
            ctx = ctx.get_context("spawn")
        self.__underlying_ctx = ctx

    def get_ctx(self) -> multiprocessing.context.BaseContext:
        return self.__underlying_ctx

    def create_queue(self) -> multiprocessing.Queue:
        return self.get_ctx().Queue()

    def support_pipe(self) -> bool:
        return True

    def create_pipe(self) -> tuple[multiprocessing.connection.Connection, multiprocessing.connection.Connection]:
        return self.get_ctx().Pipe()

    def create_event(self) -> multiprocessing.synchronize.Event:
        return self.get_ctx().Event()

    def create_worker(
        self, name: str, target: object, args: tuple, kwargs: dict[str, object]
    ) -> multiprocessing.Process:
        return self.get_ctx().Process(
            name=name, target=target, args=args, kwargs=kwargs
        )


class ManageredProcessContext(ProcessContext):
    managers: dict[object, multiprocessing.managers.SyncManager] = {}

    def get_ctx(self) -> multiprocessing.managers.SyncManager:
        underlying_ctx = super().get_ctx()
        if underlying_ctx not in self.managers:
            self.managers[underlying_ctx] = underlying_ctx.Manager()
        return self.managers[underlying_ctx]

    def create_worker(self, *args: object, **kwargs: object) -> multiprocessing.Process:
        return super().get_ctx().Process(*args, **kwargs)
