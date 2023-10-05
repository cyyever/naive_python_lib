from cyy_naive_lib.topology.central_topology import ProcessPipeCentralTopology


def test_process_task_queue():
    topology = ProcessPipeCentralTopology(worker_num=3)
    topology.send_to_worker(worker_id=1, data="abc")
    assert topology.get_from_server(worker_id=1) == "abc"
