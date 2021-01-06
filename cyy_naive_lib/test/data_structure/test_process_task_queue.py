from data_structure.process_task_queue import ProcessTaskQueue


def hello(task, args):
    assert task == ()
    return "abc"


def test_process_task_queue():
    queue = ProcessTaskQueue(hello)
    queue.start()
    queue.add_task(())
    assert queue.get_result() == "abc"
    queue.stop()
