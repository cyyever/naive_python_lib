#!/usr/bin/env python
import multiprocessing
from typing import Any

from .mp_context import MultiProcessingContext


class ProcessContext(MultiProcessingContext):
    def __init__(self, use_manager: bool = False, **kwargs):
        self.__use_manager = use_manager
        self.__manager = None
        super().__init__(**kwargs)

    def __getstate__(self):
        # capture what is normally pickled
        state = super().__getstate__()
        state["_ProcessContext__manager"] = None
        return state

    def __get_ctx(self):
        ctx = self.get_manager()
        if ctx is None:
            ctx = multiprocessing
        return ctx

    def get_manager(self):
        if not self.__use_manager:
            return None
        if self.__manager is None:
            self.__manager = multiprocessing.Manager()
        return self.__manager

    def create_queue(self) -> Any:
        return self.__get_ctx().Queue()

    def create_event(self) -> Any:
        return self.__get_ctx().Event()

    def create_worker(self, name, target, args, kwargs):
        return multiprocessing.Process(
            name=name, target=target, args=args, kwargs=kwargs
        )
