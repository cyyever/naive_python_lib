from cyy_naive_lib.concurrency import ProcessTaskQueue, ThreadTaskQueue
from cyy_naive_lib.log import log_warning


def worker(*args, **kwargs):
    log_warning("hello world")


def get_queue_types():
    queue_types = [ThreadTaskQueue, ProcessTaskQueue]
    return queue_types


def test_task_queue():
    for queue_type in get_queue_types():
        queue = queue_type(worker_num=2)
        queue.start(worker_fun=worker)
        queue.add_task(())
        queue.add_task(())
        queue.stop()
        queue.start()
        queue.force_stop()


def test_batch_task_queue():
    for queue_type in get_queue_types():
        queue = queue_type(worker_num=2, batch_process=True)
        queue.start(worker_fun=worker)
        queue.add_task(())
        queue.add_task(())
        queue.stop()
        queue.start()
        queue.force_stop()
