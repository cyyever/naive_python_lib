#!/usr/bin/env python
import threading

from .task_queue import TaskQueue


class ThreadTaskQueue(TaskQueue):
    def get_ctx(self):
        return threading
