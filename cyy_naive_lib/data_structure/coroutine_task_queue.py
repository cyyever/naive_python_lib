#!/usr/bin/env python
from typing import Callable

import gevent

from .task_queue import TaskQueue


class CoroutineTaskQueue(TaskQueue):
    def __init__(
        self,
        worker_fun: Callable = None,
        worker_num: int = 1,
    ):
        super().__init__(worker_fun=worker_fun, ctx=gevent, worker_num=worker_num)
