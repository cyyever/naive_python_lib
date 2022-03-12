#!/usr/bin/env python
import multiprocessing
from typing import Callable

from .task_queue import TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(
        self,
        worker_fun: Callable = None,
        worker_num: int = 1,
        use_manager: bool = False,
    ):
        self.use_manager = use_manager
        self.__manager = None
        super().__init__(
            worker_fun=worker_fun,
            worker_num=worker_num,
        )

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
