from typing import Any

from ..data_structure.process_context import ProcessContext
from .topology import Topology


class CentralTopology(Topology):
    def __init__(self, worker_num):
        self.worker_num = worker_num

    def get_from_server(self, worker_id: int):
        raise NotImplementedError()

    def get_from_worker(self, worker_id: int):
        raise NotImplementedError()

    def has_data_from_server(self, worker_id: int) -> bool:
        raise NotImplementedError()

    def has_data_from_worker(self, worker_id: int) -> bool:
        raise NotImplementedError()

    def send_to_server(self, worker_id: int, data):
        raise NotImplementedError()

    def send_to_worker(self, worker_id: int, data):
        raise NotImplementedError()

    def wait_close(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class ProcessPipeCentralTopology(CentralTopology):
    def __init__(
        self, *args, mp_context: ProcessContext | None = None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.__pipes: dict = {}
        if mp_context is None:
            mp_context = ProcessContext()
        self.__context = mp_context
        for worker_id in range(self.worker_num):
            # 0 => server 1=> worker
            self.__pipes[worker_id] = self.__context.create_pipe()

    def get_from_worker(self, worker_id: int) -> Any:
        assert 0 <= worker_id < self.worker_num
        return self.__pipes[worker_id][0].recv()

    def send_to_worker(self, worker_id: int, data: Any) -> None:
        return self.__pipes[worker_id][0].send(data)

    def has_data_from_worker(self, worker_id: int) -> bool:
        assert 0 <= worker_id < self.worker_num
        return self.__pipes[worker_id][0].poll()

    def get_from_server(self, worker_id: int) -> Any:
        assert 0 <= worker_id < self.worker_num
        return self.__pipes[worker_id][1].recv()

    def has_data_from_server(self, worker_id: int) -> bool:
        assert 0 <= worker_id < self.worker_num
        return self.__pipes[worker_id][1].poll()

    def send_to_server(self, worker_id: int, data: Any) -> None:
        assert 0 <= worker_id < self.worker_num
        return self.__pipes[worker_id][1].send(data)

    def wait_close(self) -> None:
        return

    def close(self) -> None:
        for p in self.__pipes.values():
            p[0].close()
            p[1].close()
