from .task_queue import TaskQueue
from .thread_context import ThreadContext


class ThreadTaskQueue(TaskQueue):
    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(mp_ctx=ThreadContext(), **kwargs)
