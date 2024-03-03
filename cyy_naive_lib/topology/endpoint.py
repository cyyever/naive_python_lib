from .topology import Topology


class Endpoint:
    def __init__(self, topology: Topology) -> None:
        self._topology: Topology = topology
