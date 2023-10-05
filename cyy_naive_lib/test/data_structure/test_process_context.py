from cyy_naive_lib.data_structure.process_context import ProcessContext
from cyy_naive_lib.log import get_logger


def hello(task, **kwargs):
    assert task == ()
    get_logger().info("call from other process")
    return "abc"


def test_pipe():
    ctx = ProcessContext()
    p, q = ctx.create_pipe()
    p.send(1)
    assert q.recv() == 1
