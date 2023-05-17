import copy
import os
import queue
import traceback
from typing import Any, Callable

# import gevent.event
# import gevent.queue
import psutil
from cyy_naive_lib.log import (apply_logger_setting, get_logger,
                               get_logger_setting)
from cyy_naive_lib.time_counter import TimeCounter

from .mp_context import MultiProcessingContext


class BatchPolicy:
    def __init__(self) -> None:
        self._processing_times: dict = {}
        self.__time_counter = TimeCounter()

    def start_batch(self, **kwargs: Any) -> None:
        self.__time_counter.reset_start_time()

    def end_batch(self, batch_size: int, **kwargs: Any) -> None:
        self._processing_times[batch_size] = (
            self.__time_counter.elapsed_milliseconds() / batch_size
        )

    def adjust_batch_size(self, batch_size: int, **kwargs: Any) -> int:
        if (
            batch_size + 1 not in self._processing_times
            or self._processing_times[batch_size + 1]
            < self._processing_times[batch_size]
        ):
            return batch_size + 1
        return batch_size


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
    def __call__(
        self, *, log_setting: dict, task_queue: Any, ppid: int, **kwargs: Any
    ) -> None:
        if log_setting:
            apply_logger_setting(log_setting)
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

    def process(self, task_queue: Any, worker_id: int, **kwargs: Any) -> bool:
        task = task_queue.get_task(timeout=3600)
        if isinstance(task, _SentinelTask):
            return True
        res = task_queue.worker_fun(
            task=task,
            **kwargs,
            worker_id=worker_id,
            worker_queue=task_queue.get_worker_queue(worker_id),
        )
        if res is not None:
            task_queue.put_data(res)
        return False


class BatchWorker(Worker):
    def __init__(self) -> None:
        super().__init__()
        self.batch_size: int = 1

    def process(
        self,
        task_queue: Any,
        worker_id: int,
        batch_policy: BatchPolicy | None = None,
        **kwargs: Any,
    ) -> bool:
        if batch_policy is None:
            batch_policy = BatchPolicy()
        assert self.batch_size > 0
        end_process = False
        tasks = []
        for idx in range(self.batch_size):
            try:
                if idx == 0:
                    task = task_queue.get_task(timeout=3600)
                elif task_queue.has_task():
                    task = task_queue.get_task(timeout=0.00001)
                else:
                    break
                if isinstance(task, _SentinelTask):
                    end_process = True
                    break
                tasks.append(task)
                task = None
            except queue.Empty:
                break
        if not tasks:
            return end_process
        batch_size = len(tasks)
        if not end_process and batch_policy is not None:
            batch_policy.start_batch(batch_size=batch_size, **kwargs)
        res = task_queue.worker_fun(
            tasks=tasks,
            worker_id=worker_id,
            worker_queue=task_queue.get_worker_queue(worker_id),
            **kwargs,
        )
        if not end_process and batch_policy is not None:
            batch_policy.end_batch(batch_size=batch_size, **kwargs)
        if res is not None:
            task_queue.put_data(res)
        if not end_process and batch_policy is not None:
            self.batch_size = batch_policy.adjust_batch_size(
                batch_size=batch_size, **kwargs
            )
        return end_process


class TaskQueue:
    def __init__(
        self,
        mp_ctx: MultiProcessingContext,
        worker_num: int = 1,
        worker_fun: Callable | None = None,
        batch_process: bool = False,
        use_worker_queue: bool = False,
    ) -> None:
        self.__mp_ctx = mp_ctx
        self.__worker_num: int = worker_num
        self.__worker_fun: Callable | None = worker_fun
        self.__workers: None | dict = None
        self._batch_process: bool = batch_process
        self.__stop_event: Any | None = None
        self.__queues: dict = {}
        self.use_worker_queue = use_worker_queue
        if self.__worker_fun is not None:
            self.start()

    @property
    def stopped(self) -> bool:
        if self.__stop_event is None:
            return True
        return self.__stop_event.is_set()

    @property
    def worker_num(self):
        return self.__worker_num

    def get_worker_queue(self, worker_id):
        return self.get_queue(name=f"__worker{worker_id}")

    def _create_queue(self) -> Any:
        return self.__mp_ctx.create_queue()

    def __getstate__(self) -> dict:
        # capture what is normally pickled
        state = self.__dict__.copy()
        state["_TaskQueue__workers"] = None
        return state

    @property
    def worker_fun(self):
        return self.__worker_fun

    def set_worker_fun(self, worker_fun: Callable) -> None:
        self.__worker_fun = worker_fun
        self.stop()
        self.start()

    def add_queue(self, name: str) -> None:
        assert name not in self.__queues
        self.__queues[name] = self._create_queue()

    def get_queue(self, name: str, default: Any = None) -> Any:
        return self.__queues.get(name, default)

    def start(self) -> None:
        assert self.__worker_num > 0
        assert self.__worker_fun is not None
        if self.__stop_event is None:
            self.__stop_event = self.__mp_ctx.create_event()
        if not self.__queues:
            self.__queues = {}
        if "__task" not in self.__queues:
            self.add_queue("__task")
        if "__result" not in self.__queues:
            self.add_queue("__result")

        if not self.__workers:
            self.__stop_event.clear()
            self.__workers = {}
        for _ in range(len(self.__workers), self.__worker_num):
            worker_id = max(self.__workers.keys(), default=-1) + 1
            self.__start_worker(worker_id)

    def put_data(self, data: Any, queue_name: str = "__result") -> None:
        result_queue = self.get_queue(queue_name)
        self.__put_data(data=data, queue=result_queue)

    @classmethod
    def __put_data(cls, data: Any, queue: Any) -> None:
        if isinstance(data, RepeatedResult):
            for _ in range(data.num):
                queue.put(data.data)
        else:
            queue.put(data)

    def __start_worker(self, worker_id: int) -> None:
        assert self.__workers is not None and worker_id not in self.__workers
        if self.use_worker_queue:
            queue_name = f"__worker{worker_id}"
            self.add_queue(queue_name)
        if self._batch_process:
            target: Worker = BatchWorker()
        else:
            target = Worker()

        self.__workers[worker_id] = self.__mp_ctx.create_worker(
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
        for q in [
            self.get_worker_queue(worker_id)
            for worker_id in range(len(self.__workers), self.__worker_num)
        ] + [self.get_queue("__result")]:
            if q is None:
                continue
            while not q.empty():
                q.get()

    def force_stop(self):
        self.__stop_event.set()
        self.stop()
        self.__stop_event.clear()

    def release(self):
        self.stop()

    def add_task(self, task: Any) -> None:
        self.put_data(task, queue_name="__task")

    def get_task(self, timeout: float) -> Any:
        return self.get_data(queue_name="__task", timeout=timeout)

    def has_task(self) -> bool:
        return self.has_data(queue_name="__task")

    def get_data(
        self, queue_name: str = "__result", timeout: float | None = None
    ) -> Any:
        result_queue = self.get_queue(queue_name)
        return result_queue.get(timeout=timeout)

    def has_data(self, queue_name: str = "__result") -> bool:
        return not self.get_queue(queue_name).empty()

    def _get_task_kwargs(self, worker_id: int) -> dict:
        return {
            "log_setting": get_logger_setting(),
            "task_queue": self,
            "worker_id": worker_id,
            "ppid": os.getpid(),
        }
