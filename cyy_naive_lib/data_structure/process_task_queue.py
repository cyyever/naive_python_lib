#!/usr/bin/env python
import multiprocessing

from .task_queue import TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(self, use_manager: bool = False, **kwargs: dict):
        self.use_manager = use_manager
        self.__manager = None
        super().__init__(**kwargs)

    def __getstate__(self):
        # capture what is normally pickled
        state = super().__getstate__()
        state["_ProcessTaskQueue__manager"] = None
        return state

    def get_ctx(self):
        return multiprocessing

    def get_manager(self):
        if self.use_manager:
            if self.__manager is None:
                self.__manager = self.get_ctx().Manager()
            return self.__manager
        return None
