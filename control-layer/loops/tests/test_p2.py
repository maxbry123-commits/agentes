from loops.capability_router import CapabilityRouter
from loops.contracts.capability import CapabilityRequest
from loops.metrics import LoopMetrics
from loops.replay import EventReplayer
from loops.contracts.types import LoopEvent
from loops.event_chain import compute_hash
from loops.simulator import LoopSimulator, ChaosMonkey
from loops.engine import LoopEngine
from loops.contracts.types import LoopContext


def test_capability_router():
    r = CapabilityRouter()
    r.register("coder", ["code_generation", "debugging"], priority=10)
    r.register("gen", ["code_generation"], priority=50)
    req = CapabilityRequest("q1", "R1", "code_generation", "t")
    res = r.resolve(req)
    assert res.ok and res.agent_id == "coder"


def test_metrics():
    m = LoopMetrics()
    m.record_run(closed=True, state="CLOSED", iterations=3, project_id="P1")
    s = m.snapshot()
    assert s["runs_closed"] == 1 and s["success_rate"] == 1.0


def test_replay():
    h0 = compute_hash("e1", "R", "LOOP_LOCKED", {}, "")
    e1 = LoopEvent("e1", "R", "LOOP_LOCKED", "t", "", h0)
    h1 = compute_hash("e2", "R", "PHASE_STARTED", {}, h0)
    e2 = LoopEvent("e2", "R", "PHASE_STARTED", "t", h0, h1)
    rr = EventReplayer().replay([e1, e2])
    assert rr.final_state == "RUNNING"


def test_simulator_happy():
    s = LoopSimulator()
    r = s.scenario_happy_close()
    assert r.ok


def test_chaos_idempotent():
    eng = LoopEngine.with_default_policy()
    ctx = LoopContext(
        run_id="R-c", loop_id="L", project_id="P", agent_id="A",
        task_id="T", goal_id="G", created_at="t", updated_at="t",
        idempotency_key="k1",
    )
    r1, r2 = ChaosMonkey().duplicate_iteration(eng, ctx)
    assert r2.cache_hit
