from cyy_naive_lib.concurrency import ProcessContext


def test_pipe():
    ctx = ProcessContext()
    p, q = ctx.create_pipe()
    p.send(1)
    assert q.recv() == 1
