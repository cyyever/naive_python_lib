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


class Worker:
    def __call__(self, log_files, task_queue, ppid, **kwargs) -> None:
        for log_file in log_files:
            set_file_handler(log_file)
        while not task_queue.stopped:
            try:
                if self.process(task_queue, **kwargs):
                    break
            except queue.Empty:
                if not psutil.pid_exists(ppid):
                    get_logger().error("exit because parent process %s has died", ppid)
                    break
                continue
            except Exception as e:
                get_logger().error("catch exception:%s", e)
                get_logger().error("traceback:%s", traceback.format_exc())
                get_logger().error("end worker on exception")
                return

    def process(self, task_queue, worker_id, **kwargs) -> bool:
        task = task_queue.get_task(timeout=3600)
        if isinstance(task, _SentinelTask):
            return True
        res = task_queue.worker_fun(
            task,
            **kwargs,
            worker_id=worker_id,
            worker_queue=task_queue.get_worker_queue(worker_id),
        )
        if res is not None:
            task_queue.put_data(res)
        return False


class BatchWorker(Worker):
    def __init__(self):
        super().__init__()
        self.batch_size = 1

    def process(
        self, task_queue, worker_id, batch_policy=None, batch_size=None, **kwargs
    ) -> bool:
        if batch_size is not None:
            self.batch_size = batch_size
        assert self.batch_size > 0
        end_process = False
        tasks = []
        for idx in range(self.batch_size):
            try:
                if idx == 0:
                    task = task_queue.get_task(timeout=3600)
                elif task_queue.has_task():
                    task = task_queue.get_task(timeout=0.00001)
                if isinstance(task, _SentinelTask):
                    end_process = True
                    break
                tasks.append(task)
            except queue.Empty:
                break
        if not tasks:
            return end_process
        batch_size = len(tasks)
        if batch_policy is not None:
            batch_policy.start_batch(batch_size=batch_size, **kwargs)
        res = task_queue.worker_fun(
            tasks,
            worker_id=worker_id,
            worker_queue=task_queue.get_worker_queue(worker_id),
            **kwargs,
        )
        if batch_policy is not None:
            self.batch_size = batch_policy.adjust_batch_size(
                batch_size=batch_size, **kwargs
            )
        if res is not None:
            task_queue.put_data(res)
        return end_process


class TaskQueue:
    def __init__(
        self,
        worker_num: int = 1,
        worker_fun: Callable = None,
        batch_process: bool = False,
        use_worker_queue: bool = False,
    ):
        self.__stop_event = None
        self.__task_queue = None
        self.__queues: dict = {}
        self.__worker_queues: dict = {}
        self.__worker_num = worker_num
        self.__worker_fun = worker_fun
        self.__workers = None
        self._batch_process = batch_process
        self.use_worker_queue = use_worker_queue
        if self.__worker_fun is not None:
            self.start()

    @property
    def stopped(self) -> bool:
        return self.__stop_event.is_set()

    @property
    def worker_num(self):
        return self.__worker_num

    def get_ctx(self):
        raise NotImplementedError()

    def get_manager(self):
        return None

    def get_worker_queue(self, worker_id):
        return self.__worker_queues.get(worker_id, None)

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
        return state

    @property
    def worker_fun(self):
        return self.__worker_fun

    def set_worker_fun(self, worker_fun):
        self.__worker_fun = worker_fun
        self.stop()
        self.start()

    def add_queue(self, name: str) -> None:
        assert name not in self.__queues
        self.__queues[name] = self.__create_queue()

    def get_queue(self, name):
        return self.__queues[name]

    def start(self):
        assert self.__worker_num > 0
        assert self.__worker_fun is not None
        ctx = self.get_ctx()
        if self.__stop_event is None:
            if ctx is gevent:
                self.__stop_event = gevent.event.Event()
            else:
                self.__stop_event = ctx.Event()
        if self.__task_queue is None:
            self.__task_queue = self.__create_queue()
        if not self.__queues:
            self.__queues: dict = {"default": self.__create_queue()}

        if not self.__workers:
            self.__stop_event.clear()
            self.__workers = {}
            for q in (self.__task_queue, *self.__queues.values()):
                while not q.empty():
                    q.get()
        for _ in range(len(self.__workers), self.__worker_num):
            worker_id = max(self.__workers.keys(), default=-1) + 1
            self.__start_worker(worker_id)

    def put_data(self, data, queue_name: str = "default"):
        self.__put_data(data=data, queue=self.get_queue(queue_name))

    @classmethod
    def __put_data(cls, data, queue):
        if isinstance(data, RepeatedResult):
            for _ in range(data.num):
                queue.put(data.data)
        else:
            queue.put(data)

    def __start_worker(self, worker_id):
        assert worker_id not in self.__workers
        if self.use_worker_queue:
            self.__worker_queues[worker_id] = self.__create_queue()
        worker_creator_fun = None
        use_process = False
        ctx = self.get_ctx()
        if self._batch_process:
            worker = BatchWorker()
        else:
            worker = Worker()
        if hasattr(ctx, "Thread"):
            worker_creator_fun = ctx.Thread
        elif hasattr(ctx, "Process"):
            worker_creator_fun = ctx.Process
            use_process = True
        elif ctx is gevent:
            self.__workers[worker_id] = gevent.spawn(
                worker,
                set(),
                **self._get_task_kwargs(worker_id),
            )
            return
        else:
            raise RuntimeError("Unsupported context:" + str(ctx))

        self.__workers[worker_id] = worker_creator_fun(
            name=f"worker {worker_id}",
            target=worker,
            args=(get_log_files() if use_process else set(),),
            kwargs=self._get_task_kwargs(worker_id),
        )
        self.__workers[worker_id].start()

    def join(self):
        if not self.__workers:
            return
        for worker in self.__workers.values():
            worker.join()

    def stop(self, wait_task=True):
        # stop __workers
        if not self.__workers:
            return
        for _ in self.__workers:
            self.add_task(_SentinelTask())
        # block until all tasks are done
        if wait_task:
            self.join()
        self.__workers = {}

    def force_stop(self):
        self.__stop_event.set()
        self.stop()
        self.__stop_event.clear()

    def release(self):
        self.stop()

    def add_task(self, task):
        self.__task_queue.put(task)

    def get_task(self, timeout):
        return self.__task_queue.get(timeout=timeout)

    def has_task(self) -> bool:
        return not self.__task_queue.empty()

    def get_result(self, queue_name: str = "default"):
        result_queue = self.get_queue(queue_name)
        return result_queue.get()

    def has_result(self, queue_name: str = "default") -> bool:
        result_queue = self.get_queue(queue_name)
        return not result_queue.empty()

    def get_data(self, queue_name: str = "default"):
        result_queue = self.get_queue(queue_name)
        return result_queue.get()

    def has_data(self, queue_name: str = "default") -> bool:
        result_queue = self.get_queue(queue_name)
        return not result_queue.empty()

    def _get_task_kwargs(self, worker_id) -> dict:
        return {"task_queue": self, "worker_id": worker_id, "ppid": os.getpid()}
