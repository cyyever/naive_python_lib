from typing import Any

from cyy_torch_toolbox.data_structure.torch_process_task_queue import \
    TorchProcessTaskQueue

from .topology import Topology


class PeerToPeerTopology(Topology):
    def __init__(self, worker_num):
        self.worker_num = worker_num

    def get_from_peer(self, my_id: int, peer_id: int) -> Any:
        raise NotImplementedError()

    def peer_end_has_data(self, my_id: int, peer_id: int) -> bool:
        raise NotImplementedError()

    def send_to_peer(self, my_id: int, peer_id: int, data: Any) -> None:
        raise NotImplementedError()


class ProcessPeerToPeerTopology(PeerToPeerTopology):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__queues: dict = {}
        for worker_id in range(self.worker_num):
            self.__queues[worker_id] = TorchProcessTaskQueue(worker_num=0)
            for peer_id in range(self.worker_num):
                self.__queues[worker_id].add_result_queue(f"result_{peer_id}")
        self.__global_lock = None

    def create_global_lock(self):
        self.__global_lock = self.get_queue(0).get_manager().RLock()

    @property
    def global_lock(self):
        return self.__global_lock

    def get_queue(self, peer_id):
        return self.__queues[peer_id]

    def get_from_peer(self, my_id, peer_id):
        assert 0 <= my_id < self.worker_num
        assert 0 <= peer_id < self.worker_num
        return self.get_queue(peer_id).get_result(queue_name=f"result_{my_id}")

    def peer_end_has_data(self, my_id: int, peer_id: int) -> bool:
        assert 0 <= my_id < self.worker_num
        assert 0 <= peer_id < self.worker_num
        return self.get_queue(peer_id).has_result(queue_name=f"result_{my_id}")

    def send_to_peer(self, my_id: int, peer_id: int, data: Any) -> None:
        assert 0 <= my_id < self.worker_num
        assert 0 <= peer_id < self.worker_num
        return self.get_queue(my_id).put_result(
            result=data, queue_name=f"result_{peer_id}"
        )

    def close(self, my_id: int) -> None:
        self.get_queue(my_id).stop()
