import time

from cyy_naive_lib.data_structure.process_context import \
    ManageredProcessContext
from cyy_naive_lib.data_structure.process_task_queue import ProcessTaskQueue
from cyy_naive_lib.log import get_logger


def hello(task, **kwargs):
    assert task == ()
    get_logger().info("call from other process")
    return "abc"


def test_process_task_queue():
    queue = ProcessTaskQueue(worker_num=8)
    queue.start(worker_fun=hello)
    queue.add_task(())
    time.sleep(1)
    assert queue.has_data()
    assert queue.get_data()[0] == "abc"
    queue.stop()
    queue = ProcessTaskQueue(worker_num=8, mp_ctx=ManageredProcessContext())
    queue.start(worker_fun=hello)
    queue.add_task(())
    assert queue.get_data()[0] == "abc"
    queue.stop()
