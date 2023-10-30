from typing import Any

from .process_context import ProcessContext
from .task_queue import TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(self, mp_ctx=ProcessContext(), **kwargs: Any):
        super().__init__(mp_ctx=mp_ctx, **kwargs)
