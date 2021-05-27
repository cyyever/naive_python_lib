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
        super().__init__(
            worker_fun=worker_fun,
            ctx=multiprocessing,
            worker_num=worker_num,
            manager=None if not use_manager else multiprocessing.Manager(),
        )
