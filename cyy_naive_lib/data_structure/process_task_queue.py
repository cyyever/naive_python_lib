from typing import Any

from .process_context import ProcessContext
from .task_queue import TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(self, use_manager: bool = False, **kwargs: Any):
        super().__init__(mp_ctx=ProcessContext(use_manager=use_manager), **kwargs)
