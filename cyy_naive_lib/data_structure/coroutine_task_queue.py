#!/usr/bin/env python
from typing import Callable

import gevent

from .task_queue import TaskQueue


class CoroutineTaskQueue(TaskQueue):
    def get_ctx(self):
        return gevent
