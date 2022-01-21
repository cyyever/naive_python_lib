#!/usr/bin/env python
import gevent

from .task_queue import TaskQueue


class CoroutineTaskQueue(TaskQueue):
    def get_ctx(self):
        return gevent
