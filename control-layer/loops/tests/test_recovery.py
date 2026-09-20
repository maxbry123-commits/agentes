"""Recovery engine tests · 0% LLM"""
from loops.contracts.types import LoopContext, PolicyDecision
from loops.recovery import RecoveryEngine


def _ctx(**kw):
    b = dict(run_id="R1", loop_id="L01", project_id="P", agent_id="A", task_id="T", goal_id="G",
             recovery_state={"repair_count": 0}, budgets={"retry_budget": 2})
    b.update(kw)
    return LoopContext(**b)


def test_repair_increments():
    eng = RecoveryEngine()
    d = PolicyDecision(action="REPAIR", run_id="R1", reason="x", decided_at="t")
    r = eng.apply(_ctx(), d)
    assert r.next_state == "REPAIRING"
    assert r.ctx_updates["recovery_state"]["repair_count"] == 1


def test_repair_exhausted_escalates():
    eng = RecoveryEngine()
    d = PolicyDecision(action="REPAIR", run_id="R1", reason="x", decided_at="t")
    r = eng.apply(_ctx(recovery_state={"repair_count": 2}), d)
    assert r.escalate
    assert r.next_state == "ESCALATED"


def test_change_strategy():
    eng = RecoveryEngine()
    d = PolicyDecision(action="CHANGE_STRATEGY", run_id="R1", reason="s", decided_at="t",
                       params={"new_strategy": "consensus"})
    r = eng.apply(_ctx(), d)
    assert r.ctx_updates["strategy"] == "consensus"
    assert r.next_state == "RUNNING"


def test_abort():
    eng = RecoveryEngine()
    d = PolicyDecision(action="ABORT", run_id="R1", reason="bad", decided_at="t")
    r = eng.apply(_ctx(), d)
    assert r.next_state == "FAILED"
