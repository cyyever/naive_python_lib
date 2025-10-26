from typing import Any

from cyy_naive_lib.concurrency import (
    ProcessTaskQueue,
    RetryableBatchPolicy,
    TaskQueue,
    ThreadTaskQueue,
)
from cyy_naive_lib.log import log_warning


def worker(task: Any, **kwargs: Any) -> Any:
    assert task == ()
    log_warning("hello world")
    return "abc"


def batch_worker(tasks: Any, **kwargs: Any) -> Any:
    log_warning("hello world")
    return ["abc"] * len(tasks)


def get_queue_types() -> list[type[TaskQueue]]:
    queue_types = [ThreadTaskQueue, ProcessTaskQueue]
    return queue_types


def test_task_queue() -> None:
    for queue_type in get_queue_types():
        queue = queue_type(worker_num=2)
        queue.start(worker_fun=worker)
        queue.add_task(())
        queue.add_task(())
        queue.stop()
        queue.start()
        queue.force_stop()


def test_batch_task_queue() -> None:
    for queue_type in get_queue_types():
        queue = queue_type(worker_num=1, batch_policy_type=RetryableBatchPolicy)
        queue.start(worker_fun=batch_worker)
        tasks = list(range(5))
        for task in tasks:
            queue.add_task(task)
        for _ in tasks:
            data = queue.get_data()
            assert data.is_ok() and data.value() == "abc"
        queue.stop()
