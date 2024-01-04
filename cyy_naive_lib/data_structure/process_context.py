import multiprocessing
from typing import Any

from ..system_info import get_operating_system
from .mp_context import MultiProcessingContext


class ProcessContext(MultiProcessingContext):
    def __init__(self, ctx: Any = multiprocessing) -> None:
        if hasattr(ctx, "get_context"):
            match get_operating_system():
                case "freebsd" | "macos":
                    ctx = ctx.get_context("fork")
                case "windows":
                    ctx = ctx.get_context("spawn")
        self.__underlying_ctx = ctx

    def get_ctx(self) -> Any:
        return self.__underlying_ctx

    def create_queue(self) -> multiprocessing.Queue:
        return self.get_ctx().Queue()

    def support_pipe(self) -> bool:
        return True

    def create_pipe(self) -> tuple:
        return self.get_ctx().Pipe()

    def create_event(self) -> Any:
        return self.get_ctx().Event()

    def create_worker(self, name: str, target: Any, args: list, kwargs: dict) -> Any:
        return self.get_ctx().Process(
            name=name, target=target, args=args, kwargs=kwargs
        )


class ManageredProcessContext(ProcessContext):
    managers: dict = {}

    def get_ctx(self) -> Any:
        underlying_ctx = super().get_ctx()
        if underlying_ctx not in self.managers:
            self.managers[underlying_ctx] = underlying_ctx.Manager()
        return self.managers[underlying_ctx]

    def support_pipe(self) -> bool:
        return False

    def create_worker(self, *args, **kwargs) -> Any:
        return super().get_ctx().Process(*args, **kwargs)
