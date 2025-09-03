from typing import Any

from .endpoint import Endpoint
from .peer_to_peer_topology import PeerToPeerTopology


class PeerEndpoint(Endpoint):
    def __init__(self, topology: PeerToPeerTopology, worker_id: int):
        super().__init__(topology=topology)
        self.__worker_id: int = worker_id

    @property
    def topology(self) -> PeerToPeerTopology:
        assert isinstance(self._topology, PeerToPeerTopology)
        return self._topology

    def all_peers(self):
        return (
            worker_id
            for worker_id in range(self.topology.worker_num)
            if worker_id != self.__worker_id
        )

    def get(self, peer_id: int) -> Any:
        return self.topology.get_from_peer(my_id=self.__worker_id, peer_id=peer_id)

    def has_data(self, peer_id: int) -> bool:
        return self.topology.peer_end_has_data(my_id=self.__worker_id, peer_id=peer_id)

    def send(self, peer_id: int, data: Any) -> None:
        self.topology.send_to_peer(my_id=self.__worker_id, peer_id=peer_id, data=data)

    def broadcast(self, data: Any) -> None:
        for worker_id in self.all_peers():
            self.send(peer_id=worker_id, data=data)

    def gather(self) -> dict:
        res: dict = {}
        for worker_id in self.all_peers():
            res[worker_id] = self.get(peer_id=worker_id)
        return res

    def close(self) -> None:
        self.topology.close(self.__worker_id)
