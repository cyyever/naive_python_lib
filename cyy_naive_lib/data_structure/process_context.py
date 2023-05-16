import multiprocessing
from typing import Any

from .mp_context import MultiProcessingContext


class ProcessContext(MultiProcessingContext):
    managers = {}

    def __init__(self, ctx=multiprocessing, use_manager: bool = False, **kwargs):
        self.__underlying_ctx = ctx
        self.__use_manager = use_manager
        # self.__manager = None
        super().__init__(**kwargs)

    # def __getstate__(self):
    #     # capture what is normally pickled
    #     state = super().__getstate__()
    #     state["_ProcessContext__manager"] = None
    #     return state

    def get_ctx(self):
        ctx = self.get_manager()
        if ctx is None:
            ctx = self.__underlying_ctx
        return ctx

    def get_manager(self):
        if not self.__use_manager:
            return None
        if self.__underlying_ctx not in self.managers:
            self.managers[self.__underlying_ctx] = self.__underlying_ctx.Manager()
        return self.managers[self.__underlying_ctx]

    def create_queue(self) -> Any:
        return self.get_ctx().Queue()

    def create_event(self) -> Any:
        return self.get_ctx().Event()

    def create_worker(self, name, target, args, kwargs):
        return self.__underlying_ctx.Process(
            name=name, target=target, args=args, kwargs=kwargs
        )
