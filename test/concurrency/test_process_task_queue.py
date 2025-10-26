import time

from cyy_naive_lib.concurrency import (
    BatchPolicy,
    ManageredProcessContext,
    ProcessTaskQueue,
    ThreadTaskQueue,
)
from cyy_naive_lib.log import log_info


def hello(task, **kwargs):
    assert task == ()
    log_info("call from other process")
    return "abc"


def batch_hello(tasks, **kwargs):
    assert tasks
    log_info("call from other process")
    return ["abc" for _ in tasks]


def get_queue_types():
    queue_types = [ThreadTaskQueue, ProcessTaskQueue]
    return queue_types


def test_process_task_queue():
    for queue_type in get_queue_types():
        queue = queue_type(worker_num=8)
        queue.start(worker_fun=hello)
        queue.add_task(())
        time.sleep(1)
        assert queue.has_data()
        data = queue.get_data()
        assert data.is_ok() and data.value() == "abc"
        queue.stop()
        queue = ProcessTaskQueue(worker_num=8, mp_ctx=ManageredProcessContext())
        queue.start(worker_fun=hello)
        queue.add_task(())
        data = queue.get_data()
        assert data.is_ok() and data.value() == "abc"
        queue.stop()


def test_task_queue_batch_process():
    for queue_type in get_queue_types():
        queue = queue_type(worker_num=1,batch_policy_type=BatchPolicy)
        queue.start(worker_fun=batch_hello)
        tasks = list(range(5))
        for task in tasks:
            queue.add_task(task)
        for _ in tasks:
            data = queue.get_data()
            assert data.is_ok() and data.value() == "abc"
        queue.stop()
