from collections.abc import Iterable

from .task_queue import TaskQueue


def batch_process(queue: TaskQueue, tasks: Iterable[object]) -> dict:
    assert not queue.has_data()
    result: dict = {}
    cnt = 0
    for task in tasks:
        queue.add_task(task)
        cnt += 1
        while queue.has_data():
            cnt -= 1
            data = queue.get_data()
            assert data.is_ok()
            assert isinstance(data.value(), dict)
            result |= data.value()
    while cnt > 0:
        data = queue.get_data()
        assert data.is_ok()
        assert isinstance(data.value(), dict)
        result |= data.value()
        cnt -= 1
    return result
