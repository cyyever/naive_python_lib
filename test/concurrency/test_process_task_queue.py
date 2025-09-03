import time

from cyy_naive_lib.concurrency import ManageredProcessContext, ProcessTaskQueue
from cyy_naive_lib.log import log_info


def hello(task, **kwargs):
    assert task == ()
    log_info("call from other process")
    return "abc"


def test_process_task_queue():
    queue = ProcessTaskQueue(worker_num=8)
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
