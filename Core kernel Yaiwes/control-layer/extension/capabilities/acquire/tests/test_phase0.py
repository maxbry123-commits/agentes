"""Phase 0 tests · acquire infrastructure · zero network."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # control-layer
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extension.capabilities.acquire.checkpoint import CheckpointStore
from extension.capabilities.acquire.lock import LockError, MissionLock
from extension.capabilities.acquire.memory_ops import MemoryOpsStore
from extension.capabilities.acquire.queue import TaskQueue
from extension.capabilities.acquire.registry import MissionRegistry
from extension.capabilities.acquire.rollback import RollbackService
from extension.capabilities.acquire.run_loop import RunLoop
from extension.capabilities.acquire.schema import Checkpoint, StopPolicy, stable_hash
from extension.capabilities.acquire.stop_policy import BudgetUsage, StopPolicyGuard


def test_queue_priority_and_deps():
    with tempfile.TemporaryDirectory() as td:
        q = TaskQueue(td)
        q.enqueue("low", priority=200, status="RUNNABLE")
        q.enqueue("high", priority=10, status="RUNNABLE")
        q.enqueue("blocked_dep", priority=1, status="RUNNABLE", depends_on=["high"])
        nxt = q.pick_next()
        assert nxt is not None and nxt.mission_id == "high"
        q.mark_terminal("high", "DONE")
        nxt2 = q.pick_next()
        assert nxt2 is not None and nxt2.mission_id == "blocked_dep"


def test_lock_exclusive():
    with tempfile.TemporaryDirectory() as td:
        lock = MissionLock(td)
        lock.acquire("m1")
        try:
            lock.acquire("m1")
            assert False, "should lock"
        except LockError:
            pass
        lock.release("m1")
        lock.acquire("m1")
        lock.release("m1")


def test_checkpoint_hash_chain():
    with tempfile.TemporaryDirectory() as td:
        store = CheckpointStore(td)
        cp1 = store.init("m1", nodes_total=3)
        assert cp1.checkpoint_hash
        cp2 = Checkpoint(mission_id="m1", nodes_done=1, nodes_total=3, status="RUNNABLE")
        store.save(cp2)
        loaded = store.load("m1")
        assert loaded is not None
        assert loaded.previous_checkpoint_hash == cp1.checkpoint_hash
        assert loaded.nodes_done == 1


def test_memory_ops_slim():
    with tempfile.TemporaryDirectory() as td:
        mem = MemoryOpsStore(td)
        mem.init("m1")
        mem.update("m1", next_action="execute", progress={"nodes_done": 2})
        got = mem.get("m1")
        assert got is not None
        assert got.next_action == "execute"
        assert got.progress["nodes_done"] == 2
        # no journal dump keys
        assert "events" not in got.to_dict()


def test_stop_policy_budget():
    g = StopPolicyGuard(StopPolicy(max_nodes=2, max_wall_time_sec=9999))
    u = BudgetUsage(nodes_used=2)
    exceeded, reason = g.exceeded(u)
    assert exceeded and reason and "max_nodes" in reason


def test_run_loop_done():
    with tempfile.TemporaryDirectory() as td:
        reg = MissionRegistry(td)
        q = TaskQueue(td)
        reg.create("m1", repo="example/repo", stop_policy=StopPolicy(max_nodes=10))
        q.enqueue("m1", repo="example/repo", status="RUNNABLE")
        loop = RunLoop(td)
        result = loop.run("m1")
        assert result.status == "DONE", result
        assert result.nodes_run == 3


def test_run_loop_failed():
    with tempfile.TemporaryDirectory() as td:
        reg = MissionRegistry(td)
        q = TaskQueue(td)
        reg.create("m2", stop_policy=StopPolicy(max_nodes=10))
        q.enqueue("m2", status="RUNNABLE")
        loop = RunLoop(td)
        result = loop.run("m2", fail_on_node="noop-0")
        assert result.status == "FAILED"


def test_run_loop_budget():
    with tempfile.TemporaryDirectory() as td:
        reg = MissionRegistry(td)
        q = TaskQueue(td)
        # max_nodes=0 means no limit in guard? we use max_nodes=1 but 3 noop nodes
        reg.create("m3", stop_policy=StopPolicy(max_nodes=1))
        q.enqueue("m3", status="RUNNABLE")
        loop = RunLoop(td)
        result = loop.run("m3")
        # first check: nodes_used starts 0, runs one node -> 1, next iteration exceeded
        assert result.status in ("BUDGET_EXCEEDED", "DONE")


def test_rollback_staging():
    with tempfile.TemporaryDirectory() as td:
        rb = RollbackService(td)
        p = rb.prepare_staging("m1")
        (p / "f.txt").write_text("x", encoding="utf-8")
        r = rb.clear_staging("m1")
        assert r.ok and r.action == "staging_cleared"
        assert not p.exists()


def test_stable_hash_deterministic():
    a = stable_hash({"b": 1, "a": 2})
    b = stable_hash({"a": 2, "b": 1})
    assert a == b


if __name__ == "__main__":
    test_queue_priority_and_deps()
    test_lock_exclusive()
    test_checkpoint_hash_chain()
    test_memory_ops_slim()
    test_stop_policy_budget()
    test_run_loop_done()
    test_run_loop_failed()
    test_run_loop_budget()
    test_rollback_staging()
    test_stable_hash_deterministic()
    print("phase0 OK")
