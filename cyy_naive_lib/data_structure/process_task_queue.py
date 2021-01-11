#!/usr/bin/env python
import multiprocessing
from typing import Callable

from .task_queue import TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(
        self,
        worker_fun: Callable,
        worker_num: int = 1,
    ):
        super().__init__(
            worker_fun=worker_fun, ctx=multiprocessing, worker_num=worker_num
        )
