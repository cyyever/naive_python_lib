#!/usr/bin/env python

from .coroutine_context import CoroutineContext
from .task_queue import TaskQueue


class CoroutineTaskQueue(TaskQueue):
    def __init__(self, **kwargs: dict):
        super().__init__(mp_ctx=CoroutineContext(), **kwargs)
