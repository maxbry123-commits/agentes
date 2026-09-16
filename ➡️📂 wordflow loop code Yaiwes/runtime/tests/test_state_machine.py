"""
tests/core/test_state_machine.py
Tests unitarios de src/core/state_machine.py — T-001 (archivo 4/4)
"""

from __future__ import annotations

import asyncio

import pytest

from src.core.state_machine import (
    InvalidTransitionError,
    NodeState,
    StateMachine,
    UnknownStateError,
)


def test_initial_state_is_pending() -> None:
    sm = StateMachine()
    assert sm.get_state("n1") == NodeState.PENDING


def test_valid_transition_pending_to_running() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        result = await sm.transition("n1", "RUNNING")
        assert result == NodeState.RUNNING
        assert sm.get_state("n1") == NodeState.RUNNING

    asyncio.run(scenario())


def test_full_lifecycle_pending_running_done() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        await sm.transition("n1", "RUNNING")
        await sm.transition("n1", "DONE")
        assert sm.get_state("n1") == NodeState.DONE
        assert sm.is_terminal("n1") is True

    asyncio.run(scenario())


def test_invalid_transition_pending_to_done_raises() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        with pytest.raises(InvalidTransitionError):
            await sm.transition("n1", "DONE")

    asyncio.run(scenario())


def test_invalid_transition_from_terminal_state_raises() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        await sm.transition("n1", "RUNNING")
        await sm.transition("n1", "DONE")
        with pytest.raises(InvalidTransitionError):
            await sm.transition("n1", "RUNNING")

    asyncio.run(scenario())


def test_unknown_state_string_raises() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        with pytest.raises(UnknownStateError):
            await sm.transition("n1", "NOT_A_REAL_STATE")

    asyncio.run(scenario())


def test_retry_after_failure_allowed() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        await sm.transition("n1", "RUNNING")
        await sm.transition("n1", "FAILED")
        result = await sm.transition("n1", "RUNNING")
        assert result == NodeState.RUNNING

    asyncio.run(scenario())


def test_history_records_all_transitions_in_order() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        await sm.transition("n1", "RUNNING")
        await sm.transition("n1", "DONE")
        hist = sm.history("n1")
        assert [r.to_state for r in hist] == [NodeState.RUNNING, NodeState.DONE]
        assert hist[0].from_state == NodeState.PENDING
        assert hist[1].from_state == NodeState.RUNNING

    asyncio.run(scenario())


def test_history_is_a_copy_not_live_reference() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        await sm.transition("n1", "RUNNING")
        hist = sm.history("n1")
        hist.append("corrupted")  # type: ignore[arg-type]
        assert len(sm.history("n1")) == 1

    asyncio.run(scenario())


def test_reset_returns_node_to_pending() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        await sm.transition("n1", "RUNNING")
        await sm.transition("n1", "FAILED")
        await sm.reset("n1")
        assert sm.get_state("n1") == NodeState.PENDING
        assert sm.history("n1") == []

    asyncio.run(scenario())


def test_multiple_nodes_are_independent() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        await sm.transition("n1", "RUNNING")
        assert sm.get_state("n1") == NodeState.RUNNING
        assert sm.get_state("n2") == NodeState.PENDING

    asyncio.run(scenario())


def test_blocked_state_roundtrip() -> None:
    async def scenario() -> None:
        sm = StateMachine()
        await sm.transition("n1", "RUNNING")
        await sm.transition("n1", "BLOCKED")
        result = await sm.transition("n1", "RUNNING")
        assert result == NodeState.RUNNING

    asyncio.run(scenario())
