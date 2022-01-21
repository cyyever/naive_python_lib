#!/usr/bin/env python3
import copy
import os
import queue
import threading
import traceback
from typing import Callable

import gevent.event
import gevent.queue
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
    def __init__(self, worker_num: int = 1, worker_fun: Callable = None):
        self.stop_event = None
        self.task_queue = self.__create_queue()
        self.__result_queues: dict = {"default": self.__create_queue()}
        self.worker_num = worker_num
        self.__worker_fun = worker_fun
        self.__workers = None
        if self.__worker_fun is not None:
            self.start()

    def get_ctx(self):
        raise NotImplementedError()

    def get_manager(self):
        return None

    def __create_queue(self):
        manager = self.get_manager()
        if manager is not None:
            return manager.Queue()
        ctx = self.get_ctx()
        if ctx is threading:
            return queue.Queue()
        if ctx is gevent:
            return gevent.queue.Queue()
        return ctx.Queue()

    def __getstate__(self):
        # capture what is normally pickled
        state = self.__dict__.copy()
        state["_TaskQueue__workers"] = None
        # state["_TaskQueue__manager"] = None
        # state["_TaskQueue__ctx"] = None
        return state

    @property
    def worker_fun(self):
        return self.__worker_fun

    def set_worker_fun(self, worker_fun):
        self.__worker_fun = worker_fun
        self.stop()
        self.start()

    def add_result_queue(self, name: str):
        assert name not in self.__result_queues
        self.__result_queues[name] = self.__create_queue()

    def get_result_queue(self, name):
        return self.__result_queues[name]

    def start(self):
        assert self.worker_num > 0
        assert self.__worker_fun is not None
        if self.stop_event is None:
            ctx = self.get_ctx()
            if ctx is gevent:
                self.stop_event = gevent.event.Event()
            else:
                self.stop_event = ctx.Event()

        if not self.__workers:
            self.stop_event.clear()
            self.__workers = {}
            for q in (self.task_queue, *self.__result_queues.values()):
                while not q.empty():
                    q.get()
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
        ctx = self.get_ctx()
        if hasattr(ctx, "Process"):
            worker_creator_fun = ctx.Process
            use_process = True
        elif hasattr(ctx, "Thread"):
            worker_creator_fun = ctx.Thread
        elif ctx is gevent:
            self.__workers[worker_id] = gevent.spawn(
                work,
                self,
                os.getpid(),
                set(),
                self._get_extra_task_arguments(worker_id),
            )
            return
        else:
            raise RuntimeError("Unsupported context:" + str(ctx))

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
        # stop __workers
        self.send_sentinel_task(self.worker_num)
        if not self.__workers:
            return
        # block until all tasks are done
        if wait_task:
            self.join()
        self.__workers = {}

    def force_stop(self):
        self.stop_event.set()
        self.stop()
        self.stop_event.clear()

    def add_task(self, task):
        self.task_queue.put(task)

    def get_result(self, queue_name: str = "default"):
        result_queue = self.get_result_queue(queue_name)
        return result_queue.get()

    def has_result(self, queue_name: str = "default") -> bool:
        result_queue = self.get_result_queue(queue_name)
        return not result_queue.empty()

    def _get_extra_task_arguments(self, worker_id):
        return {"queue": self, "worker_id": worker_id}
