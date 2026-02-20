from collections.abc import Iterable

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

    def get(self, worker_id: int) -> object:
        return self.topology.get_from_worker(worker_id=worker_id)

    def send(self, worker_id: int, data: object) -> None:
        self.topology.send_to_worker(worker_id=worker_id, data=data)

    def __construct_worker_ids(
        self, worker_ids: None | Iterable[int] = None
    ) -> set[int]:
        all_worker_ids = set(range(self.worker_num))
        if worker_ids is None:
            return all_worker_ids
        return set(worker_ids).intersection(all_worker_ids)

    def broadcast(self, data: object, worker_ids: None | Iterable[int] = None) -> None:
        for worker_id in self.__construct_worker_ids(worker_ids=worker_ids):
            self.send(worker_id=worker_id, data=data)

    def poll(self, worker_ids: None | Iterable[int] = None) -> dict[int, object]:
        res = {}
        for worker_id in self.__construct_worker_ids(worker_ids=worker_ids):
            if self.has_data(worker_id=worker_id):
                res[worker_id] = self.get(worker_id=worker_id)
        return res

    def close(self) -> None:
        self.topology.close_server_channel()


class ClientEndpoint(Endpoint):
    def __init__(self, topology: CentralTopology, worker_id: int) -> None:
        super().__init__(topology=topology)
        self.__worker_id: int = worker_id

    @property
    def topology(self) -> CentralTopology:
        assert isinstance(self._topology, CentralTopology)
        return self._topology

    def get(self) -> object:
        return self.topology.get_from_server(self.__worker_id)

    def has_data(self) -> bool:
        return self.topology.has_data_from_server(self.__worker_id)

    def send(self, data: object) -> None:
        self.topology.send_to_server(worker_id=self.__worker_id, data=data)

    def close(self) -> None:
        self.topology.close_worker_channel(worker_id=self.__worker_id)
