from .topology import Topology


class Endpoint:
    def __init__(self, topology: Topology):
        self._topology: Topology = topology
