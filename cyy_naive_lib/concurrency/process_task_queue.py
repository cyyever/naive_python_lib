from typing import Any

from .process_context import ProcessContext
from .task_queue import TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(self, **kwargs: Any) -> None:
        if "mp_ctx" not in kwargs:
            kwargs["mp_ctx"] = ProcessContext()
        super().__init__(**kwargs)
