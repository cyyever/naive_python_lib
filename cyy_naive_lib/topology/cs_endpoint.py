from typing import Any, Iterable

from .central_topology import CentralTopology
from .endpoint import Endpoint


class ServerEndpoint(Endpoint):
    @property
    def topology(self) -> CentralTopology:
        assert isinstance(self._topology, CentralTopology)
        return self._topology

    @property
    def worker_num(self) -> int:
        return self.topology.worker_num

    def has_data(self, worker_id: int) -> bool:
        return self.topology.has_data_from_worker(worker_id=worker_id)

    def get(self, worker_id: int) -> Any:
        return self.topology.get_from_worker(worker_id=worker_id)

    def send(self, worker_id: int, data: Any) -> None:
        self.topology.send_to_worker(worker_id=worker_id, data=data)

    def broadcast(self, data: Any, worker_ids: None | Iterable = None) -> None:
        all_worker_ids = set(range(self.worker_num))
        if worker_ids is None:
            worker_ids = all_worker_ids
        else:
            worker_ids = set(worker_ids).intersection(all_worker_ids)
        for worker_id in worker_ids:
            self.send(worker_id=worker_id, data=data)

    def close(self) -> None:
        assert isinstance(self._topology, CentralTopology)
        self._topology.close_server_channel()


class ClientEndpoint(Endpoint):
    def __init__(self, topology: CentralTopology, worker_id: int) -> None:
        super().__init__(topology=topology)
        assert isinstance(self._topology, CentralTopology)
        self.__worker_id: int = worker_id

    @property
    def topology(self) -> CentralTopology:
        assert isinstance(self._topology, CentralTopology)
        return self._topology

    def get(self) -> Any:
        return self.topology.get_from_server(self.__worker_id)

    def has_data(self) -> bool:
        return self.topology.has_data_from_server(self.__worker_id)

    def send(self, data: Any) -> None:
        self.topology.send_to_server(worker_id=self.__worker_id, data=data)

    def close(self) -> None:
        self.topology.close_worker_channel(worker_id=self.__worker_id)
