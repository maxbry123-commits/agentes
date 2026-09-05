from loops.detectors import NativeDetectors
from loops.event_chain import verify_chain, compute_hash
from loops.contracts.types import LoopEvent
from loops.lease_backend import InProcessLeaseBackend


def test_native_stall():
    d = NativeDetectors(stall_window=3)
    assert d.observe("r", 0.01) == []
    assert d.observe("r", 0.02) == []
    out = d.observe("r", 0.01)
    assert any(x.detector == "stall" for x in out)


def test_chain_verify():
    h0 = compute_hash("e1", "R", "LOOP_CREATED", {}, "")
    e1 = LoopEvent("e1", "R", "LOOP_CREATED", "t", "", h0)
    h1 = compute_hash("e2", "R", "LOOP_LOCKED", {}, h0)
    e2 = LoopEvent("e2", "R", "LOOP_LOCKED", "t", h0, h1)
    ok, reason = verify_chain([e1, e2])
    assert ok, reason


def test_lease_backend():
    b = InProcessLeaseBackend()
    assert b.acquire("r1", "w1", 30) is not None
    assert b.acquire("r1", "w2", 30) is None
    assert b.renew("r1", "w1", 30)
    assert b.release("r1", "w1")
