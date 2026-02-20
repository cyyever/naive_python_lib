from ..concurrency import ProcessTaskQueue
from ..function import Expected
from .topology import Topology


class PeerToPeerTopology(Topology):
    def __init__(self, worker_num: int) -> None:
        self.worker_num = worker_num

    def get_from_peer(self, my_id: int, peer_id: int) -> Expected:
        raise NotImplementedError

    def peer_end_has_data(self, my_id: int, peer_id: int) -> bool:
        raise NotImplementedError

    def send_to_peer(self, my_id: int, peer_id: int, data: object) -> None:
        raise NotImplementedError

    def close(self, my_id: int) -> None:
        raise NotImplementedError


class ProcessPeerToPeerTopology(PeerToPeerTopology):
    def __init__(
        self, task_queue_type: type[ProcessTaskQueue], *args: int, **kwargs: int
    ) -> None:
        super().__init__(*args, **kwargs)
        self.__queues: dict = {}
        for worker_id in range(self.worker_num):
            self.__queues[worker_id] = task_queue_type(worker_num=0)
            for peer_id in range(self.worker_num):
                self.__queues[worker_id].add_result_queue(f"result_{peer_id}")

    def get_queue(self, peer_id: int) -> ProcessTaskQueue:
        return self.__queues[peer_id]

    def get_from_peer(self, my_id: int, peer_id: int):
        assert 0 <= my_id < self.worker_num
        assert 0 <= peer_id < self.worker_num
        return self.get_queue(peer_id).get_data(queue_name=f"result_{my_id}")

    def peer_end_has_data(self, my_id: int, peer_id: int) -> bool:
        assert 0 <= my_id < self.worker_num
        assert 0 <= peer_id < self.worker_num
        return self.get_queue(peer_id).has_data(queue_name=f"result_{my_id}")

    def send_to_peer(self, my_id: int, peer_id: int, data: object) -> None:
        assert 0 <= my_id < self.worker_num
        assert 0 <= peer_id < self.worker_num
        return self.get_queue(my_id).put_data(data=data, queue_name=f"result_{peer_id}")

    def close(self, my_id: int) -> None:
        self.get_queue(my_id).stop()
