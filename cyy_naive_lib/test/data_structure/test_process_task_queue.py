import asyncio
import time

from log import get_logger

from data_structure.process_task_queue import ProcessTaskQueue


def hello(task, args):
    assert task == ()
    get_logger().info("call from other process")
    return "abc"


def test_process_task_queue():
    queue = ProcessTaskQueue(worker_fun=hello, worker_num=8)
    queue.start()
    queue.add_task(())
    time.sleep(1)
    assert queue.has_result()
    assert queue.get_result() == "abc"
    queue.stop()
    queue = ProcessTaskQueue(worker_fun=hello, worker_num=8, use_manager=True)
    queue.start()
    queue.add_task(())
    assert queue.get_result() == "abc"
    queue.stop()
    queue = ProcessTaskQueue(worker_fun=hello, worker_num=8, use_manager=True)
    queue.start()
    queue.add_task(())
    assert asyncio.run(queue.get_result_async()) == "abc"
    queue.stop()
