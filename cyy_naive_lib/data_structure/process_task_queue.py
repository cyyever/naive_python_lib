#!/usr/bin/env python3
import multiprocessing
import traceback
from typing import Callable

from log import default_logger


class _SentinelTask:
    pass


class RepeatedResult:
    def __init__(self, data, num):
        self.data = data
        self.num = num


def worker(
    task_queue, result_queue, processor_fun: Callable, stop_event, extra_arguments: list
):
    while not stop_event.is_set():
        task = task_queue.get()
        if isinstance(task, _SentinelTask):
            break
        try:
            res = processor_fun(task, extra_arguments)
            if res is not None:
                if isinstance(res, RepeatedResult):
                    for _ in range(res.num):
                        result_queue.put(res.data)
                else:
                    result_queue.put(res)
        except Exception as e:
            default_logger.error("catch exception:%s", e)
            default_logger.error("traceback:%s", traceback.format_exc())


class ProcessTaskQueue:
    def __init__(
        self, processor_fun: Callable, ctx=multiprocessing, worker_num: int = 1
    ):
        self.ctx = ctx
        self.task_queue = self.ctx.Queue()
        self.result_queue = self.ctx.Queue()
        self.stop_event = self.ctx.Event()
        self.worker_num = worker_num
        self.processor_fun = processor_fun
        self.processors: dict = dict()
        self.start()

    def start(self):
        for worker_id in range(len(self.processors), self.worker_num):
            t = self.ctx.Process(
                target=worker,
                args=(
                    self.task_queue,
                    self.result_queue,
                    self.processor_fun,
                    self.stop_event,
                    self._get_extra_task_arguments(worker_id),
                ),
            )
            self.processors[worker_id] = t
            t.start()

    def join(self):
        for processor in self.processors.values():
            processor.join()

    def stop(self):
        if not self.processors:
            return
        # stop workers
        for _ in range(self.worker_num):
            self.add_task(_SentinelTask())
        # block until all tasks are done
        self.join()
        self.processors = dict()

    def force_stop(self):
        self.stop_event.set()
        self.stop()
        self.stop_event.clear()

    def add_task(self, task):
        self.task_queue.put(task)

    def get_result(self):
        return self.result_queue.get()

    def _get_extra_task_arguments(self, worker_id):
        return [worker_id]
