from cyy_naive_lib.concurrency import (ProcessTaskQueue, ThreadTaskQueue,
                                       batch_process)


def worker(task, **kwargs):
    return {task: task}


def get_queue_types():
    queue_types = [ThreadTaskQueue, ProcessTaskQueue]
    return queue_types


def test_batch_task_queue():
    for queue_type in get_queue_types():
        queue = queue_type(worker_num=2)
        queue.start(worker_fun=worker)
        tasks = list(range(5))
        res = batch_process(queue, tasks)
        queue.stop()
        assert res == dict(zip(tasks, tasks))
