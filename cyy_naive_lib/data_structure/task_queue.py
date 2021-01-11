#!/usr/bin/env python3
import queue
import threading
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
    task_queue, result_queue, worker_fun: Callable, stop_event, extra_arguments: list
):
    while not stop_event.is_set():
        task = task_queue.get()
        if isinstance(task, _SentinelTask):
            break
        try:
            res = worker_fun(task, extra_arguments)
            if res is not None:
                if isinstance(res, RepeatedResult):
                    for _ in range(res.num):
                        result_queue.put(res.data)
                else:
                    result_queue.put(res)
        except Exception as e:
            default_logger.error("catch exception:%s", e)
            default_logger.error("traceback:%s", traceback.format_exc())


class TaskQueue:
    def __init__(
        self,
        worker_fun: Callable,
        ctx,
        worker_num: int = 1,
    ):
        self.ctx = ctx
        if ctx is threading:
            self.task_queue = queue.Queue()
            self.result_queue = queue.Queue()
        else:
            self.task_queue = self.ctx.Queue()
            self.result_queue = self.ctx.Queue()
        self.stop_event = self.ctx.Event()
        self.worker_num = worker_num
        self.worker_fun = worker_fun
        self.workers: dict = dict()
        self.start()

    def start(self):
        for worker_id in range(len(self.workers), self.worker_num):
            creator_fun = None
            if hasattr(self.ctx, "Process"):
                creator_fun = self.ctx.Process
            elif hasattr(self.ctx, "Thread"):
                creator_fun = self.ctx.Thread
            else:
                raise RuntimeError("Unsupported context:" + str(self.ctx))

            self.workers[worker_id] = creator_fun(
                target=worker,
                args=(
                    self.task_queue,
                    self.result_queue,
                    self.worker_fun,
                    self.stop_event,
                    self._get_extra_task_arguments(worker_id),
                ),
            )
            self.workers[worker_id].start()

    def join(self):
        for worker in self.workers.values():
            worker.join()

    def stop(self, wait_task=True):
        if not self.workers:
            return
        # stop workers
        for _ in range(self.worker_num):
            self.add_task(_SentinelTask())
        # block until all tasks are done
        if wait_task:
            self.join()
        for worker in self.workers.values():
            worker.join()
        self.workers = dict()

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
