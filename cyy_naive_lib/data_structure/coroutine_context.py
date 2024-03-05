from typing import Any, Callable

import gevent
import gevent.event
import gevent.queue

from .mp_context import MultiProcessingContext


class CoroutineContext(MultiProcessingContext):
    def create_queue(self) -> gevent.queue.Queue:
        return gevent.queue.Queue()

    def create_pipe(self) -> Any:
        raise NotImplementedError()

    def create_event(self) -> gevent.event.Event:
        return gevent.event.Event()

    def create_worker(
        self, name: str, target: Callable, args: Any, kwargs: Any
    ) -> gevent.Greenlet:
        worker = gevent.spawn(target, *args, **kwargs)
        return worker
