try:
    from cyy_naive_lib.data_structure.coroutine_task_queue import \
        CoroutineTaskQueue

    has_gevent = True
except BaseException:
    has_gevent = False
from cyy_naive_lib.data_structure.process_task_queue import ProcessTaskQueue
from cyy_naive_lib.data_structure.thread_task_queue import ThreadTaskQueue
from cyy_naive_lib.log import get_logger


def worker(*args, **kwargs):
    get_logger().warning("hello world")


def get_queue_types():
    queue_types = [ThreadTaskQueue, ProcessTaskQueue]
    if has_gevent:
        queue_types.append(CoroutineTaskQueue)
    return queue_types


def test_task_queue():
    for queue_type in get_queue_types():
        queue = queue_type(worker_fun=worker, worker_num=2)
        queue.start()
        queue.add_task(())
        queue.add_task(())
        queue.stop()
        queue.start()
        queue.force_stop()


def test_batch_task_queue():
    for queue_type in get_queue_types():
        queue = queue_type(worker_fun=worker, worker_num=2, batch_process=True)
        queue.start()
        queue.add_task(())
        queue.add_task(())
        queue.stop()
        queue.start()
        queue.force_stop()
