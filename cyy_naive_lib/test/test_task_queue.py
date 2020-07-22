from task_queue import TaskQueue


def test_task_queue():
    queue = TaskQueue(lambda task: print("hello world"), 2)
    queue.start()
    queue.add_task(())
    queue.stop()
    queue.start()
    queue.force_stop()
