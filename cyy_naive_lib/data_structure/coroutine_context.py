import gevent
import gevent.event
import gevent.queue

from .mp_context import MultiProcessingContext


class CoroutineContext(MultiProcessingContext):
    def create_queue(self) -> gevent.queue.Queue:
        return gevent.queue.Queue()

    def create_event(self):
        return gevent.event.Event()

    def create_worker(self, name, target, args, kwargs):
        worker = gevent.spawn(target, *args, **kwargs)
        worker.name = name
        return worker
