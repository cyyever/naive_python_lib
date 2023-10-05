import multiprocessing
from typing import Any

from ..system_info import get_operating_system
from .mp_context import MultiProcessingContext


class ProcessContext(MultiProcessingContext):
    managers: dict = {}

    def __init__(
        self, ctx: Any = multiprocessing, use_manager: bool = False, **kwargs: Any
    ) -> None:
        if hasattr(ctx, "get_context"):
            match get_operating_system():
                case "freebsd" | "macos":
                    ctx = ctx.get_context("fork")
                case "windows":
                    ctx = ctx.get_context("spawn")
        self.__underlying_ctx = ctx
        self.__use_manager = use_manager
        super().__init__(**kwargs)

    def get_ctx(self) -> Any:
        ctx = self.get_manager()
        if ctx is None:
            ctx = self.__underlying_ctx
        return ctx

    def get_manager(self) -> Any | None:
        if not self.__use_manager:
            return None
        if self.__underlying_ctx not in self.managers:
            self.managers[self.__underlying_ctx] = self.__underlying_ctx.Manager()
        return self.managers[self.__underlying_ctx]

    def create_queue(self) -> multiprocessing.Queue:
        return self.get_ctx().Queue()

    def create_pipe(self) -> multiprocessing.Pipe:
        return self.get_ctx().Pipe()

    def create_event(self) -> Any:
        return self.get_ctx().Event()

    def create_worker(self, name: str, target: Any, args: list, kwargs: dict) -> Any:
        return self.__underlying_ctx.Process(
            name=name, target=target, args=args, kwargs=kwargs
        )
