from .process_context import ProcessContext
from .task_queue import TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        if "mp_ctx" not in kwargs:
            kwargs["mp_ctx"] = ProcessContext()
        super().__init__(**kwargs)
