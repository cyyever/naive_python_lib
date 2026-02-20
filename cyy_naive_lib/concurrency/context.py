import multiprocessing
import multiprocessing.connection
import multiprocessing.synchronize
import queue
import threading
from collections.abc import Callable


class ConcurrencyContext:
    def create_queue(self) -> multiprocessing.Queue | queue.Queue:
        raise NotImplementedError

    def in_thread(self) -> bool:
        return False

    def support_pipe(self) -> bool:
        return False

    def create_pipe(self) -> tuple:
        raise NotImplementedError

    def create_event(self) -> threading.Event | multiprocessing.synchronize.Event:
        raise NotImplementedError

    def create_thread(
        self, name: str, target: Callable, args: tuple, kwargs: dict[str, object]
    ) -> threading.Thread:
        return threading.Thread(name=name, target=target, args=args, kwargs=kwargs)

    def create_worker(
        self, name: str, target: Callable, args: tuple, kwargs: dict[str, object]
    ) -> threading.Thread | multiprocessing.Process:
        raise NotImplementedError
