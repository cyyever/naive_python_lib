from data_structure.process_task_queue import ProcessTaskQueue
from data_structure.thread_task_queue import ThreadTaskQueue


def test_task_queue():
    for queue_type in [ThreadTaskQueue, ProcessTaskQueue]:
        queue = queue_type(lambda task, _: print("hello world"), 2)
        queue.start()
        queue.add_task(())
        queue.stop()
        queue.start()
        queue.force_stop()
