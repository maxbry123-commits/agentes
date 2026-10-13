"""Tests deterministas state machine · 0% LLM"""
from loops.contracts.types import LoopContext, can_transition, assert_transition, TERMINAL
from loops.state_machine import StateMachine, check_invariants, InvariantError


def _ctx(**kw):
    base = dict(
        run_id="R1",
        loop_id="L01",
        project_id="P1",
        agent_id="A1",
        task_id="T1",
        goal_id="G1",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    base.update(kw)
    return LoopContext(**base)


def test_happy_path():
    sm = StateMachine()
    ctx = _ctx()
    ctx, _ = sm.transition(ctx, "LOCKED", event_type="LOOP_LOCKED")
    assert ctx.state == "LOCKED"
    ctx, _ = sm.transition(ctx, "RUNNING", event_type="PHASE_STARTED")
    ctx, _ = sm.transition(ctx, "VALIDATING", event_type="PHASE_COMPLETED")
    ctx, _ = sm.transition(ctx, "DECIDING", event_type="VALIDATION_PASSED")
    ctx, _ = sm.transition(ctx, "CLOSED", event_type="LOOP_COMPLETED")
    assert ctx.state == "CLOSED"
    assert ctx.closed_at is not None


def test_illegal_transition():
    try:
        assert_transition("CLOSED", "RUNNING")
        assert False
    except ValueError:
        pass


def test_invariant_project_immutable():
    a = _ctx(state="RUNNING")
    b = _ctx(state="RUNNING", project_id="OTHER")
    try:
        check_invariants(b, previous=a)
        assert False
    except InvariantError:
        pass


def test_can_transition_table():
    assert can_transition("CREATED", "LOCKED")
    assert not can_transition("CREATED", "RUNNING")
    assert "CLOSED" in TERMINAL
