#!/usr/bin/env python

from .task_queue import TaskQueue
from .thread_context import ThreadContext


class ThreadTaskQueue(TaskQueue):
    def __init__(self, use_manager: bool = False, **kwargs: dict):
        super().__init__(mp_ctx=ThreadContext(), **kwargs)
