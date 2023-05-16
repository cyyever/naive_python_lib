from .coroutine_context import CoroutineContext
from .task_queue import TaskQueue


class CoroutineTaskQueue(TaskQueue):
    def __init__(self, **kwargs: dict) -> None:
        super().__init__(mp_ctx=CoroutineContext(), **kwargs)
