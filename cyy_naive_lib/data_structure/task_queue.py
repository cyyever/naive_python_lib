#!/usr/bin/env python
import queue
import threading
import traceback
from typing import Callable


from log import get_logger


class _SentinelTask:
    pass


class TaskQueue(queue.Queue):
    def __init__(self, processor: Callable, worker_num: int = 1):
        queue.Queue.__init__(self)
        self.worker_num = worker_num
        self.processor = processor
        self.threads: list = []
        self.stop_event = threading.Event()
        self.start()

    def start(self):
        self.stop()
        for worker_id in range(self.worker_num):
            t = threading.Thread(
                target=self.__worker,
                args=(
                    self.stop_event,
                    self._get_extra_task_arguments(worker_id)),
            )
            self.threads.append(t)
            t.start()

    def stop(self, wait_task=True):
        if not self.threads:
            return
        # stop workers
        for _ in range(self.worker_num):
            self.put(_SentinelTask())
        # block until all tasks are done
        if wait_task:
            self.join()
        for thd in self.threads:
            thd.join()
        self.threads = []

    def force_stop(self):
        self.stop_event.set()
        self.stop(False)
        self.stop_event.clear()

    def add_task(self, task):
        self.put(task)

    def __worker(self, stop_event, extra_arguments: list):
        while not stop_event.is_set():
            task = self.get()
            if isinstance(task, _SentinelTask):
                self.task_done()
                break
            try:
                if extra_arguments:
                    self.processor(task, *extra_arguments)
                else:
                    self.processor(task)
            except Exception as e:
                get_logger().error("catch exception:%s", e)
                get_logger().error("traceback:%s", traceback.format_exc())
            self.task_done()

    def _get_extra_task_arguments(self, _):
        return []