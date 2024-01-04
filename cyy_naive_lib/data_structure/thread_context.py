import queue
import threading
from typing import Any

from .mp_context import MultiProcessingContext


class ThreadContext(MultiProcessingContext):
    def create_queue(self) -> queue.Queue:
        return queue.Queue()

    def create_pipe(self) -> Any:
        raise NotImplementedError()

    def create_event(self):
        return threading.Event()

    def create_worker(self, name, target, args, kwargs):
        return self.create_thread(name=name, target=target, args=args, kwargs=kwargs)
