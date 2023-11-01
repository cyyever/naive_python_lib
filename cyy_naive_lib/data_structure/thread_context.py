#!/usr/bin/env python
import queue
import threading

from .mp_context import MultiProcessingContext


class ThreadContext(MultiProcessingContext):
    def create_queue(self) -> queue.Queue:
        return queue.Queue()

    def create_event(self):
        return threading.Event()

    def create_worker(self, name, target, args, kwargs):
        return self.create_thread(name=name, target=target, args=args, kwargs=kwargs)
