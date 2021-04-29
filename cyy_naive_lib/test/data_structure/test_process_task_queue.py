from data_structure.process_task_queue import ProcessTaskQueue
from log import get_logger


def hello(task, args):
    assert task == ()
    get_logger().info("call from other process")
    return "abc"


def test_process_task_queue():
    queue = ProcessTaskQueue(hello, worker_num=8)
    queue.start()
    queue.add_task(())
    assert queue.get_result() == "abc"
    queue.stop()
