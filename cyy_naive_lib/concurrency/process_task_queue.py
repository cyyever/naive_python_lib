from .context import ConcurrencyContext
from .process_context import ProcessContext
from .task_queue import BatchPolicy, TaskQueue


class ProcessTaskQueue(TaskQueue):
    def __init__(
        self,
        mp_ctx: ConcurrencyContext | None = None,
        worker_num: int = 1,
        batch_policy_type: type[BatchPolicy] | None = None,
    ) -> None:
        if mp_ctx is None:
            mp_ctx = ProcessContext()
        super().__init__(
            mp_ctx=mp_ctx, worker_num=worker_num, batch_policy_type=batch_policy_type
        )
