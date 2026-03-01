import copy
import math
import multiprocessing.context
import multiprocessing.synchronize
import os
import threading
import traceback
from collections.abc import Callable
from enum import StrEnum, auto
from types import TracebackType
from typing import Self

import psutil

from cyy_naive_lib.log import (
    log_debug,
    log_error,
    propagate_to_process,
)

from cyy_naive_lib.time_counter import TimeCounter

from ..function import Expected
from .context import ConcurrencyContext
from .process_context import ProcessContext


class QueueType(StrEnum):
    Pipe = auto()
    Queue = auto()


class BatchPolicy:
    def __init__(self) -> None:
        self._mean_processing_times: dict = {}
        self.__time_counter: TimeCounter = TimeCounter()
        self._current_batch_size: int | None = None

    def _start_batch(self) -> None:
        assert self._current_batch_size is not None
        self.__time_counter.reset_start_time()

    def _end_batch(self) -> None:
        assert self._current_batch_size is not None
        batch_size = self._current_batch_size
        new_mean_time = self.__time_counter.elapsed_milliseconds() / batch_size
        if batch_size in self._mean_processing_times:
            new_mean_time = (
                self._mean_processing_times[batch_size] + new_mean_time
            ) / 2
        self._mean_processing_times[batch_size] = new_mean_time
        self._current_batch_size = None

    def _cancel_batch(self) -> None:
        self._current_batch_size = None

    def explore_batch_size(self, initial_batch_size: int) -> int:
        assert initial_batch_size >= 1, initial_batch_size
        batch_size = initial_batch_size
        assert batch_size in self._mean_processing_times
        # if (
        #     batch_size > 1
        #     and self._mean_processing_times[batch_size]
        #     > self._mean_processing_times[batch_size - 1]
        # ):
        #     batch_size -= 1
        while (
            batch_size + 1 not in self._mean_processing_times
            or math.fabs(
                self._mean_processing_times[batch_size + 1]
                - self._mean_processing_times[batch_size]
            )
            / self._mean_processing_times[batch_size]
            < 0.1
        ):
            batch_size += 1
            if batch_size not in self._mean_processing_times:
                return batch_size
        return batch_size

    def set_current_batch_size(self, batch_size: int) -> None:
        assert batch_size >= 1, batch_size
        self._current_batch_size = batch_size

    def __enter__(self) -> Self:
        assert self._current_batch_size is not None
        self._start_batch()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_value is None:
            self._end_batch()
        else:
            self._cancel_batch()


class RetryableBatchPolicy(BatchPolicy):
    def __init__(self) -> None:
        super().__init__()
        self._no_workable_batch_sizes: set[int] = set()

    def set_current_batch_size(self, batch_size: int) -> None:
        assert self.is_batch_size_allowed(batch_size)
        super().set_current_batch_size(batch_size)

    def is_batch_size_allowed(self, batch_size: int) -> bool:
        return all(
            batch_size < no_workable_batch_size
            for no_workable_batch_size in self._no_workable_batch_sizes
        )

    def explore_batch_size(self, initial_batch_size: int) -> int:
        batch_size = super().explore_batch_size(initial_batch_size)
        if batch_size > 1:
            while not self.is_batch_size_allowed(batch_size):
                batch_size -= 1
        assert batch_size >= 1
        return batch_size

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_value is not None:
            assert self._current_batch_size is not None
            log_error("Forbid batch size %s", self._current_batch_size)
            self._no_workable_batch_sizes.add(self._current_batch_size)
        super().__exit__(exc_type, exc_value, traceback)


class _SentinelTask:
    pass


class RepeatedResult:
    def __init__(self, data: object, num: int, copy_data: bool = True) -> None:
        self.__data = data
        self.__num = num
        self.__copy_data = copy_data

    def get_data_list(self) -> list[object]:
        return [self.data for _ in range(self.__num)]

    def set_data(self, data: object) -> None:
        self.__data = data

    @property
    def data(self) -> object:
        if self.__copy_data:
            return copy.deepcopy(self.__data)
        return self.__data


class Worker:
    def __call__(
        self,
        *,
        task_queue: "TaskQueue",
        ppid: int,
        worker_id: int,
        **kwargs: object,
    ) -> None:
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

    def _get_task(self, task_queue: "TaskQueue", timeout: float) -> Expected:
        task = task_queue.get_task(timeout=timeout)
        if task.is_ok() and isinstance(task.value(), _SentinelTask):
            return Expected.not_ok()
        return task

    def process(
        self, task_queue: "TaskQueue", worker_id: int, **kwargs: object
    ) -> bool:
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

    def __batch_process(
        self,
        tasks: list[object],
        task_queue: "TaskQueue",
        **kwargs: object,
    ) -> None:
        assert self.batch_size > 0
        batch_size = len(tasks)
        while tasks:
            batch = tasks[:batch_size]
            results: list | None = None
            try:
                log_error("use batch size %s", batch_size)
                self.batch_policy.set_current_batch_size(batch_size=batch_size)
                with self.batch_policy:
                    results = task_queue.worker_fun(
                        tasks=batch,
                        **kwargs,
                    )
                self.batch_size = self.batch_policy.explore_batch_size(
                    initial_batch_size=batch_size
                )
                assert batch_size <= self.batch_size
                log_debug("new batch_size is %s", self.batch_size)
                tasks = tasks[len(batch) :]
            except BaseException:
                log_error("Got exception", exc_info=True)
                if (
                    isinstance(self.batch_policy, RetryableBatchPolicy)
                    and batch_size > 1
                ):
                    batch_size -= 1
                    continue
                else:
                    raise
            assert results is None or len(results) == len(batch)
            if results is not None:
                for result in results:
                    task_queue.put_data(data=result, queue_name="__result")

    def __collect_tasks(self, task_queue: "TaskQueue") -> tuple[list, bool]:
        end_process = False
        tasks = []
        for idx in range(self.batch_size):
            if idx == 0:
                task = self._get_task(task_queue=task_queue, timeout=3600)
            else:
                task = self._get_task(task_queue=task_queue, timeout=0.000001)
            if not task.is_ok():
                end_process = True
                break
            tasks.append(task.value())
        return tasks, end_process

    def process(
        self,
        task_queue: "TaskQueue",
        worker_id: int,
        **kwargs: object,
    ) -> bool:
        assert self.batch_size > 0
        tasks, end_process = self.__collect_tasks(task_queue=task_queue)
        if tasks:
            self.__batch_process(
                tasks=tasks, task_queue=task_queue, worker_id=worker_id, **kwargs
            )
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
        self.__stop_event: (
            threading.Event | multiprocessing.synchronize.Event | None
        ) = None
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
    def worker_num(self) -> int:
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

    def put_data(self, data: object | RepeatedResult, queue_name: str) -> None:
        queue, queue_type = self.__get_queue(queue_name)
        data_list: list = [data]
        if isinstance(data, RepeatedResult):
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
        use_spwan = (
            use_thread
            or self.mp_ctx.in_thread()
            or (
                isinstance(self.mp_ctx, ProcessContext)
                and isinstance(
                    self.mp_ctx.get_ctx(), multiprocessing.context.SpawnContext
                )
            )
        )

        if self.__set_logger and use_spwan:
            target = propagate_to_process(target)
        self.__workers[worker_id] = creator(
            name=f"worker {worker_id}",
            target=target,
            args=(),
            kwargs=self._get_task_kwargs(worker_id),
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

    def add_task(self, task: object) -> None:
        self.put_data(data=task, queue_name="__task")

    def get_task(self, timeout: float | None) -> Expected:
        return self.get_data(queue_name="__task", timeout=timeout)

    def has_task(self) -> bool:
        return self.has_data(queue_name="__task")

    def clear_data(self, queue_name: str) -> None:
        if queue_name not in self.__queues:
            return
        while True:
            res = self.get_data(queue_name=queue_name, timeout=0.000001)
            if not res.is_ok() or res.value() is None:
                return

    def get_data(
        self, queue_name: str = "__result", timeout: float | None = None
    ) -> Expected[object]:
        res = self.__get_data(queue_name=queue_name, timeout=timeout)
        if (
            res.is_ok()
            and isinstance(res.value(), _SentinelTask)
            and queue_name != "__task"
        ):
            raise RuntimeError("Sending _SentinelTask in queue:" + queue_name)
        return res

    def __get_data(self, /, queue_name: str, timeout: float | None) -> Expected[object]:
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

    def _get_task_kwargs(self, worker_id: int) -> dict:
        return {
            "task_queue": self,
            "worker_id": worker_id,
            "ppid": os.getpid(),
        }
