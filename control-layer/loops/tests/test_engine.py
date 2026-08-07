"""LoopEngine integration smoke · 0% LLM"""
from loops.contracts.types import LoopContext
from loops.engine import LoopEngine
from loops.policy.engine import PolicyEngine


def _ctx():
    return LoopContext(
        run_id="R-test",
        loop_id="L01",
        project_id="P1",
        agent_id="A1",
        task_id="T1",
        goal_id="G1",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        budgets={"retry_budget": 2},
        recovery_state={"repair_count": 0},
    )


def test_one_iteration_closes_when_goal_complete():
    # policy: validation_passed + goal_complete → CLOSE
    eng = LoopEngine(policy=PolicyEngine([
        {
            "id": "close",
            "when": {"phase_outcome": "validation_passed", "goal_complete": True},
            "action": "CLOSE",
            "reason": "done",
        }
    ]))
    result = eng.run_iteration(_ctx(), goal_complete=True)
    assert result.closed
    assert result.ctx.state == "CLOSED"
    assert len(result.events) >= 3


def test_continue_bumps_iteration():
    eng = LoopEngine(policy=PolicyEngine([
        {
            "id": "cont",
            "when": {"phase_outcome": "validation_passed", "goal_complete": False},
            "action": "CONTINUE",
            "reason": "more",
        }
    ]))
    result = eng.run_iteration(_ctx(), goal_complete=False)
    assert result.ctx.state == "RUNNING"
    assert result.ctx.iteration == 1
