from data_structure.coroutine_task_queue import CoroutineTaskQueue
from data_structure.process_task_queue import ProcessTaskQueue
from data_structure.thread_task_queue import ThreadTaskQueue


def worker(*args):
    print("hello world")


def test_task_queue():
    for queue_type in [ThreadTaskQueue, ProcessTaskQueue, CoroutineTaskQueue]:
        queue = queue_type(worker_fun=worker,worker_num= 2)
        queue.start()
        queue.add_task(())
        queue.add_task(())
        queue.stop()
        queue.start()
        queue.force_stop()
