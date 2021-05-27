#!/usr/bin/env python
import threading
from typing import Callable

from .task_queue import TaskQueue


class ThreadTaskQueue(TaskQueue):
    def __init__(
        self,
        worker_fun: Callable = None,
        worker_num: int = 1,
    ):
        super().__init__(worker_fun=worker_fun, ctx=threading, worker_num=worker_num)
