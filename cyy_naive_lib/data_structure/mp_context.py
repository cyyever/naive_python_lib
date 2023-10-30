from typing import Any


class MultiProcessingContext:
    def create_queue(self) -> Any:
        raise NotImplementedError()

    def has_pipe(self) -> bool:
        return False

    def create_event(self) -> Any:
        raise NotImplementedError()

    def create_worker(self, name, target, args, kwargs):
        raise NotImplementedError()
