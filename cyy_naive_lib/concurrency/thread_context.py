import queue
import threading
from collections.abc import Callable

from .context import ConcurrencyContext


class ThreadContext(ConcurrencyContext):
    def create_queue(self) -> queue.Queue:
        return queue.Queue()

    def in_thread(self) -> bool:
        return True

    def create_pipe(self) -> tuple:
        raise NotImplementedError

    def create_event(self) -> threading.Event:
        return threading.Event()

    def create_worker(
        self, name: str, target: Callable, args: tuple, kwargs: dict[str, object]
    ) -> threading.Thread:
        return self.create_thread(name=name, target=target, args=args, kwargs=kwargs)
