#!/usr/bin/env python3
import copy
import os
import queue
import threading
import traceback
from typing import Callable

import psutil
from cyy_naive_lib.log import get_log_files, get_logger, set_file_handler


class _SentinelTask:
    pass


class RepeatedResult:
    def __init__(self, data, num, copy_data=True):
        self.__data = data
        self.num = num
        self.__copy_data = copy_data

    def get_data(self):
        return self.__data

    def set_data(self, data):
        self.__data = data

    @property
    def data(self):
        if self.__copy_data:
            return copy.deepcopy(self.__data)
        return self.__data


def work(
    q,
    pid,
    log_files,
    extra_arguments: list,
):
    for log_file in log_files:
        set_file_handler(log_file)
    while not q.stop_event.is_set():
        try:
            task = q.task_queue.get(3600)
            if isinstance(task, _SentinelTask):
                break
            res = q.worker_fun(task, extra_arguments)
            if res is not None:
                q.put_result(res)
        except queue.Empty:
            if not psutil.pid_exists(pid):
                get_logger().error("exit because parent process %s has died", pid)
                break
            continue
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())
            get_logger().error("end worker on exception")
            return


class TaskQueue:
    def __init__(
        self, ctx, worker_num: int = 1, worker_fun: Callable = None, manager=None
    ):
        self.__ctx = ctx
        self.__manager = manager
        if self.__manager is not None:
            self.stop_event = self.__manager.Event()
        else:
            self.stop_event = self.__ctx.Event()
        self.task_queue = self.__create_queue()
        self.__result_queues: dict = {"default": self.__create_queue()}
        self.worker_num = worker_num
        self.__worker_fun = worker_fun
        self.__workers = None
        if self.__worker_fun is not None:
            self.start()

    def __create_queue(self):
        if self.__ctx is threading:
            return queue.Queue()
        if self.__manager is not None:
            return self.__manager.Queue()
        return self.__ctx.Queue()

    @property
    def manager(self):
        return self.__manager

    def __getstate__(self):
        # capture what is normally pickled
        state = self.__dict__.copy()
        state["_TaskQueue__workers"] = None
        state["_TaskQueue__manager"] = None
        state["_TaskQueue__ctx"] = None
        return state

    @property
    def worker_fun(self):
        return self.__worker_fun

    def set_worker_fun(self, worker_fun, ctx=None):
        if ctx is not None:
            if self.__ctx is not None:
                assert self.__ctx is ctx
            else:
                self.__ctx = ctx
        self.__worker_fun = worker_fun
        self.stop()
        self.start()

    def add_result_queue(self, name: str):
        assert name not in self.__result_queues
        self.__result_queues[name] = self.__create_queue()

    def get_result_queue(self, name):
        return self.__result_queues[name]

    def start(self):
        if self.__workers is None:
            self.__workers = dict()

        for _ in range(len(self.__workers), self.worker_num):
            worker_id = max(self.__workers.keys(), default=0) + 1
            self.__start_worker(worker_id)

    def put_result(self, result, queue_name: str = "default"):
        result_queue = self.get_result_queue(queue_name)
        if isinstance(result, RepeatedResult):
            for _ in range(result.num):
                result_queue.put(result.data)
        else:
            result_queue.put(result)

    def __start_worker(self, worker_id):
        assert worker_id not in self.__workers
        worker_creator_fun = None
        use_process = False
        if hasattr(self.__ctx, "Process"):
            worker_creator_fun = self.__ctx.Process
            use_process = True
        elif hasattr(self.__ctx, "Thread"):
            worker_creator_fun = self.__ctx.Thread
        else:
            raise RuntimeError("Unsupported context:" + str(self.__ctx))

        self.__workers[worker_id] = worker_creator_fun(
            target=work,
            args=(
                self,
                os.getpid(),
                get_log_files() if use_process else set(),
                self._get_extra_task_arguments(worker_id),
            ),
        )
        self.__workers[worker_id].start()

    def join(self):
        if not self.__workers:
            return
        for worker in self.__workers.values():
            worker.join()

    def send_sentinel_task(self, number):
        for _ in range(number):
            self.add_task(_SentinelTask())

    def stop(self, wait_task=True):
        if not self.__workers:
            return
        # stop __workers
        self.send_sentinel_task(self.worker_num)
        # block until all tasks are done
        if wait_task:
            self.join()
        self.__workers = dict()

    def force_stop(self):
        self.stop_event.set()
        self.stop()
        self.stop_event.clear()

    def add_task(self, task):
        self.task_queue.put(task)

    def get_result(self, queue_name: str = "default"):
        result_queue = self.get_result_queue(queue_name)
        return result_queue.get()

    def _get_extra_task_arguments(self, worker_id):
        return [worker_id]
