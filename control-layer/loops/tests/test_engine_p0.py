"""P0 wire tests · budget stall risk cache"""
from loops.contracts.types import LoopContext
from loops.engine import LoopEngine
from loops.policy.engine import PolicyEngine
from loops.risk import RiskEngine


def _ctx(**kw):
    b = dict(
        run_id="R-p0",
        loop_id="L01",
        project_id="P",
        agent_id="A",
        task_id="T",
        goal_id="G",
        created_at="t",
        updated_at="t",
        budgets={"retry_budget": 2},
        recovery_state={"repair_count": 0},
    )
    b.update(kw)
    return LoopContext(**b)


def test_close_with_progress_and_strategy():
    eng = LoopEngine(policy=PolicyEngine([
        {"id": "c", "when": {"phase_outcome": "validation_passed", "goal_complete": True},
         "action": "CLOSE", "reason": "ok"}
    ]))
    r = eng.run_iteration(_ctx(), goal_complete=True, task_type="planning")
    assert r.closed
    assert r.progress_score is not None
    assert r.ctx.strategy  # strategy memory applied


def test_high_risk_pauses():
    eng = LoopEngine()
    r = eng.run_iteration(_ctx(), risk_actions=["delete", "deploy"])
    assert r.ctx.state == "PAUSED"


def test_idempotency_skips():
    eng = LoopEngine(policy=PolicyEngine([
        {"id": "c", "when": {"phase_outcome": "validation_passed", "goal_complete": False},
         "action": "CONTINUE", "reason": "x"}
    ]))
    c = _ctx(idempotency_key="same")
    r1 = eng.run_iteration(c, goal_complete=False)
    r2 = eng.run_iteration(r1.ctx, goal_complete=False)
    assert r2.cache_hit
