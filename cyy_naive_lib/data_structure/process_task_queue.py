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
        super().__init__(
            worker_fun=worker_fun,
            worker_num=worker_num,
        )

    def get_ctx(self):
        if self.use_manager:
            return multiprocessing.Manager()
        return multiprocessing
