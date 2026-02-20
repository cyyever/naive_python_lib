from .task_queue import BatchPolicy, TaskQueue
from .thread_context import ThreadContext


class ThreadTaskQueue(TaskQueue):
    def __init__(
        self,
        worker_num: int = 1,
        batch_policy_type: type[BatchPolicy] | None = None,
    ) -> None:
        super().__init__(
            mp_ctx=ThreadContext(),
            worker_num=worker_num,
            batch_policy_type=batch_policy_type,
        )
