#!/usr/bin/env python

from .process_context import ProcessContext
from .task_queue import TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(self, use_manager: bool = False, **kwargs: dict):
        super().__init__(mp_ctx=ProcessContext(use_manager=use_manager), **kwargs)
