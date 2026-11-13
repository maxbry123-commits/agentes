"""Tests for Feature 2: Direction-based Delegation."""

from __future__ import annotations

import pytest

from cognithor.a2a.delegation import (
    DirectedMessage,
    DirectionPermissionError,
    can_send_direction,
    direct,
    validate_direction_target,
)


class TestDirectionPermissions:
    def test_orchestrator_can_send_all(self):
        for d in ("remember", "act", "notes"):
            assert can_send_direction("orchestrator", d)

    def test_worker_can_only_send_notes(self):
        assert can_send_direction("worker", "notes")
        assert not can_send_direction("worker", "act")
        assert not can_send_direction("worker", "remember")

    def test_monitor_can_only_send_notes(self):
        assert can_send_direction("monitor", "notes")
        assert not can_send_direction("monitor", "act")

    def test_worker_cannot_send_act_to_orchestrator(self):
        """Worker role cannot send 'act' direction."""
        assert not can_send_direction("worker", "act")


class TestDirectionTargetValidation:
    def test_remember_requires_memory_tools(self):
        assert validate_direction_target("remember", {"save_to_memory", "read_file"})
        assert not validate_direction_target("remember", {"read_file", "web_search"})

    def test_act_accepts_any_worker(self):
        assert validate_direction_target("act", set())

    def test_notes_accepts_anyone(self):
        assert validate_direction_target("notes", set())


class TestDirectedMessage:
    def test_serialize_roundtrip(self):
        msg = DirectedMessage(
            direction="act",
            source_agent="planner",
            target_agent="worker-1",
            payload={"task": "research"},
        )
        d = msg.to_dict()
        msg2 = DirectedMessage.from_dict(d)
        assert msg2.direction == "act"
        assert msg2.target_agent == "worker-1"
        assert msg2.payload == {"task": "research"}

    def test_default_direction_is_act(self):
        """Messages without direction default to 'act' (backward compat)."""
        msg = DirectedMessage.from_dict({})
        assert msg.direction == "act"


class TestDirectFunction:
    @pytest.mark.asyncio
    async def test_direction_remember_writes_memory(self):
        results = []

        async def handler(msg):
            results.append(msg.direction)
            return "stored"

        r = await direct(
            source_role="orchestrator",
            target_agent="mem-worker",
            direction="remember",
            payload={"content": "test data"},
            handler=handler,
        )
        assert r.success
        assert r.result == "stored"
        assert results == ["remember"]

    @pytest.mark.asyncio
    async def test_direction_act_executes_task(self):
        async def handler(msg):
            return {"output": "done"}

        r = await direct(
            source_role="orchestrator",
            target_agent="exec-worker",
            direction="act",
            payload={"task": "run tests"},
            handler=handler,
        )
        assert r.success
        assert r.result == {"output": "done"}

    @pytest.mark.asyncio
    async def test_direction_notes_is_fire_and_forget(self):
        called = []

        async def handler(msg):
            called.append(True)

        r = await direct(
            source_role="worker",
            target_agent="monitor",
            direction="notes",
            payload={"note": "step completed"},
            handler=handler,
        )
        assert r.is_fire_and_forget
        assert called == [True]

    @pytest.mark.asyncio
    async def test_old_call_still_works(self):
        """Default direction=act works as backward compat for old .call()."""

        async def handler(msg):
            return "legacy result"

        r = await direct(
            source_role="orchestrator",
            target_agent="agent",
            direction="act",
            payload={"task": "old-style"},
            handler=handler,
        )
        assert r.success
        assert r.direction == "act"

    @pytest.mark.asyncio
    async def test_permission_error_raised(self):
        with pytest.raises(DirectionPermissionError):
            await direct(
                source_role="worker",
                target_agent="other",
                direction="act",
                payload={},
            )
