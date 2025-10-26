import copy
import os
import traceback
from collections.abc import Callable
from enum import StrEnum, auto
from typing import Any, Self

import psutil

from cyy_naive_lib.log import (
    apply_logger_setting,
    get_logger_setting,
    log_debug,
    log_error,
)
from cyy_naive_lib.time_counter import TimeCounter

from ..function import Expected
from .context import ConcurrencyContext


class QueueType(StrEnum):
    Pipe = auto()
    Queue = auto()


class BatchPolicy:
    def __init__(self) -> None:
        self._mean_processing_times: dict = {}
        self.__time_counter: TimeCounter = TimeCounter()
        self.__current_batch_size: int | None = None

    def _start_batch(self) -> None:
        assert self.__current_batch_size is not None
        self.__time_counter.reset_start_time()

    def _end_batch(self) -> None:
        assert self.__current_batch_size is not None
        batch_size = self.__current_batch_size
        self._mean_processing_times[batch_size] = (
            self.__time_counter.elapsed_milliseconds() / batch_size
        )
        self.__current_batch_size = None

    def explore_batch_size(self, initial_batch_size: int) -> int:
        assert initial_batch_size >= 1, initial_batch_size
        batch_size = initial_batch_size
        while (
            batch_size + 1 not in self._mean_processing_times
            or self._mean_processing_times[batch_size + 1]
            < self._mean_processing_times[batch_size]
        ):
            batch_size += 1
            if batch_size not in self._mean_processing_times:
                return batch_size
        return batch_size

    def set_current_batch_size(self, batch_size: int) -> None:
        assert batch_size >= 1, batch_size
        self.__current_batch_size = batch_size

    def __enter__(self) -> Self:
        assert self.__current_batch_size is not None
        self._start_batch()
        return self

    def __exit__(self, *args) -> None:
        self._end_batch()


class RetryableBatchPolicy(BatchPolicy):
    def __init__(self) -> None:
        super().__init__()
        self._no_workable_batch_sizes: set[int] = set()

    def set_current_batch_size(self, batch_size: int) -> None:
        assert self.is_batch_size_allowed(batch_size)
        super().set_current_batch_size(batch_size)

    def is_batch_size_allowed(self, batch_size: int):
        return all(
            batch_size < no_workable_batch_size
            for no_workable_batch_size in self._no_workable_batch_sizes
        )

    def explore_batch_size(self, initial_batch_size: int) -> int:
        batch_size = super().explore_batch_size(initial_batch_size)
        while not self.is_batch_size_allowed(batch_size):
            batch_size -= 1
        assert batch_size >= 1
        return batch_size


class _SentinelTask:
    pass


class RepeatedResult:
    def __init__(self, data: Any, num: int, copy_data: bool = True) -> None:
        self.__data = data
        self.__num = num
        self.__copy_data = copy_data

    def get_data_list(self) -> list:
        return [self.data for _ in range(self.__num)]

    def set_data(self, data) -> None:
        self.__data = data

    @property
    def data(self) -> None:
        if self.__copy_data:
            return copy.deepcopy(self.__data)
        return self.__data


class Worker:
    def __call__(
        self,
        *,
        log_setting: dict,
        task_queue: "TaskQueue",
        ppid: int,
        worker_id: int,
        **kwargs: Any,
    ) -> None:
        if log_setting:
            apply_logger_setting(log_setting)
        while not task_queue.stopped:
            try:
                if self.process(task_queue, worker_id=worker_id, **kwargs):
                    break
            # pylint: disable=broad-exception-caught
            except Exception as e:
                if not psutil.pid_exists(ppid):
                    log_error("exit because parent process %s has died", ppid)
                    return
                log_error("catch exception:%s", e)
                log_error("traceback:%s", traceback.format_exc())
                log_error("end worker on exception")
                return
        task_queue.clear_data(task_queue.get_worker_queue_name(worker_id))

    def _get_task(self, task_queue: "TaskQueue", timeout: float):
        task = task_queue.get_task(timeout=timeout)
        if task.is_ok() and isinstance(task.value(), _SentinelTask):
            return Expected.not_ok()
        return task

    def process(self, task_queue: "TaskQueue", worker_id: int, **kwargs: Any) -> bool:
        task = self._get_task(task_queue=task_queue, timeout=3600)
        if not task.is_ok():
            return True
        res = task_queue.worker_fun(
            task=task.value(),
            **kwargs,
            worker_id=worker_id,
        )
        if res is not None:
            task_queue.put_data(data=res, queue_name="__result")
        return False


class BatchWorker(Worker):
    def __init__(self, batch_policy: BatchPolicy) -> None:
        super().__init__()
        self.batch_size: int = 1
        self.batch_policy: BatchPolicy = batch_policy

    def process(
        self,
        task_queue: "TaskQueue",
        worker_id: int,
        **kwargs: Any,
    ) -> bool:
        assert self.batch_size > 0
        end_process = False
        tasks = []
        for idx in range(self.batch_size):
            if idx == 0:
                task = self._get_task(task_queue=task_queue, timeout=3600)
            elif task_queue.has_task():
                task = self._get_task(task_queue=task_queue, timeout=0.000001)
            else:
                break
            if not task.is_ok():
                end_process = True
                break
            tasks.append(task.value())
        if not tasks:
            return end_process
        batch_size = len(tasks)

        self.batch_policy.set_current_batch_size(batch_size=batch_size)
        results: list | None = None
        with self.batch_policy:
            res = task_queue.worker_fun(
                tasks=tasks,
                worker_id=worker_id,
                **kwargs,
            )
            assert isinstance(res, list) or res is None
            if results is None:
                results = res
            else:
                assert isinstance(res, list)
                results += res
        assert not results or len(results) == len(tasks)
        for result in results:
            task_queue.put_data(data=result, queue_name="__result")
        self.batch_size = self.batch_policy.explore_batch_size(
            initial_batch_size=batch_size
        )
        assert batch_size <= self.batch_size
        log_debug("new batch_size is %s", self.batch_size)
        return end_process


class TaskQueue:
    def __init__(
        self,
        mp_ctx: ConcurrencyContext,
        worker_num: int = 1,
        batch_policy_type: type[BatchPolicy] | None = None,
    ) -> None:
        self.__mp_ctx = mp_ctx
        self.__worker_num: int = worker_num
        self.__worker_fun: Callable | None = None
        self.__workers: None | dict = None
        self.__batch_policy_type = batch_policy_type
        self.__stop_event: Any | None = None
        self.__queues: dict = {}
        self.__set_logger: bool = True

    @property
    def mp_ctx(self) -> ConcurrencyContext:
        return self.__mp_ctx

    def disable_logger(self) -> None:
        self.__set_logger = False

    @property
    def stopped(self) -> bool:
        if self.__stop_event is None:
            return True
        return self.__stop_event.is_set()

    @property
    def worker_num(self):
        return self.__worker_num

    def get_worker_queue_name(self, worker_id: int) -> str:
        return f"__worker{worker_id}"

    def __getstate__(self) -> dict:
        # capture what is normally dilld
        state = self.__dict__.copy()
        state["_TaskQueue__workers"] = None
        return state

    @property
    def worker_fun(self) -> Callable:
        assert self.__worker_fun is not None
        return self.__worker_fun

    def add_queue(self, name: str, queue_type: QueueType) -> None:
        assert name not in self.__queues
        if queue_type == QueueType.Pipe and self.mp_ctx.support_pipe():
            self.__queues[name] = (self.mp_ctx.create_pipe(), QueueType.Pipe)
        else:
            self.__queues[name] = (self.mp_ctx.create_queue(), QueueType.Queue)

    def __get_queue(self, name: str) -> tuple:
        return self.__queues[name]

    def start(
        self, worker_fun: Callable | None = None, use_thread: bool = False
    ) -> None:
        self.stop()
        if worker_fun is not None:
            self.__worker_fun = worker_fun
        assert self.__worker_num > 0
        assert self.__worker_fun is not None
        if self.__stop_event is None:
            self.__stop_event = self.mp_ctx.create_event()
        if not self.__queues:
            self.__queues = {}
        if "__task" not in self.__queues:
            self.add_queue("__task", queue_type=QueueType.Queue)
        if "__result" not in self.__queues:
            self.add_queue("__result", queue_type=QueueType.Queue)

        if not self.__workers:
            assert self.__stop_event is not None
            self.__stop_event.clear()
            self.__workers = {}
        for _ in range(len(self.__workers), self.__worker_num):
            worker_id = max(self.__workers.keys(), default=-1) + 1
            self._start_worker(worker_id, use_thread=use_thread)

    def put_data(self, data: Any, queue_name: str) -> None:
        queue, queue_type = self.__get_queue(queue_name)
        data_list = [data]
        if hasattr(data, "get_data_list"):
            data_list = data.get_data_list()

        if queue_type == QueueType.Pipe:
            for a in data_list:
                queue[0].send(a)
        else:
            for a in data_list:
                queue.put(a)

    def _start_worker(self, worker_id: int, use_thread: bool) -> None:
        assert self.__workers is not None and worker_id not in self.__workers

        target: Worker = (
            BatchWorker(batch_policy=self.__batch_policy_type())
            if self.__batch_policy_type is not None
            else Worker()
        )
        creator = self.mp_ctx.create_worker
        if use_thread:
            creator = self.mp_ctx.create_thread
        in_thread = use_thread or self.mp_ctx.in_thread()

        self.__workers[worker_id] = creator(
            name=f"worker {worker_id}",
            target=target,
            args=(),
            kwargs=self._get_task_kwargs(worker_id, in_thread=in_thread),
        )
        self.__workers[worker_id].start()

    def join(self) -> None:
        if not self.__workers:
            return
        for worker in self.__workers.values():
            worker.join()

    def stop(self, wait_task: bool = True) -> None:
        # stop __workers
        if not self.__workers:
            return
        for _ in self.__workers:
            self.add_task(_SentinelTask())
        # block until all tasks are done
        if wait_task:
            self.join()
        self.__workers = {}
        self.__queues = {}

    def force_stop(self) -> None:
        if self.__stop_event is not None:
            self.__stop_event.set()
        self.stop()
        if self.__stop_event is not None:
            self.__stop_event.clear()

    def release(self) -> None:
        self.stop()

    def add_task(self, task: Any) -> None:
        self.put_data(data=task, queue_name="__task")

    def get_task(self, timeout: float | None) -> Expected:
        return self.get_data(queue_name="__task", timeout=timeout)

    def has_task(self) -> bool:
        return self.has_data(queue_name="__task")

    def clear_data(self, queue_name) -> None:
        if queue_name not in self.__queues:
            return
        while True:
            res = self.get_data(queue_name=queue_name, timeout=0.000001)
            if res is None:
                return

    def get_data(
        self, queue_name: str = "__result", timeout: float | None = None
    ) -> Expected[Any]:
        res = self.__get_data(queue_name=queue_name, timeout=timeout)
        if (
            res.is_ok()
            and isinstance(res.value(), _SentinelTask)
            and queue_name != "__task"
        ):
            raise RuntimeError("Sending _SentinelTask in queue:" + queue_name)
        return res

    def __get_data(self, /, queue_name: str, timeout: float | None) -> Expected[Any]:
        result_queue, queue_type = self.__get_queue(queue_name)
        try:
            if queue_type == QueueType.Pipe:
                if result_queue[1].poll(timeout):
                    res = result_queue[1].recv()
                    return Expected.ok(value=res)
                return Expected.not_ok()
            res = result_queue.get(timeout=timeout)
            return Expected.ok(value=res)
        except Exception as e:
            if (
                "empty" in e.__class__.__name__.lower()
                or "eof" in e.__class__.__name__.lower()
            ):
                return Expected.not_ok()
            raise e

    def has_data(self, queue_name: str = "__result") -> bool:
        queue, queue_type = self.__get_queue(queue_name)
        if queue_type == QueueType.Pipe:
            return queue[1].poll()
        return not queue.empty()

    def _get_task_kwargs(self, worker_id: int, in_thread: bool) -> dict:
        kwargs = {
            "task_queue": self,
            "worker_id": worker_id,
            "ppid": os.getpid(),
        }
        if self.__set_logger and not in_thread:
            kwargs["log_setting"] = get_logger_setting()
        else:
            kwargs["log_setting"] = {}
        return kwargs
