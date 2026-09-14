"""Tests für Orchestrator Runner-Verdrahtung.

Testet:
  - set_runner() speichert Callback
  - Runner erzeugt IncomingMessage mit channel="sub_agent"
  - Timeout → AgentResult(success=False)
  - _execute_delegation() liefert nicht-leeren String wenn Runner gesetzt
"""

from __future__ import annotations

import asyncio

import pytest

from cognithor.models import AgentResult, AgentType, IncomingMessage, SubAgentConfig


class TestSetRunner:
    def test_set_runner_stores_callback(self) -> None:
        """set_runner() setzt _runner."""
        from cognithor.core.orchestrator import Orchestrator

        orch = Orchestrator.__new__(Orchestrator)
        orch._runner = None
        orch._agents = {}
        orch._max_depth = 3

        async def dummy_runner(config, name):
            return AgentResult(response="ok", success=True)

        orch.set_runner(dummy_runner)
        assert orch._runner is dummy_runner


class TestRunnerMessage:
    @pytest.mark.asyncio
    async def test_runner_creates_incoming_message(self) -> None:
        """Runner erzeugt IncomingMessage mit channel='sub_agent'."""
        captured_msg = None

        async def mock_handle_message(msg: IncomingMessage):
            nonlocal captured_msg
            captured_msg = msg
            from cognithor.models import OutgoingMessage

            return OutgoingMessage(channel="sub_agent", user_id="test", text="done")

        # Build a runner like the gateway does
        async def _agent_runner(config: SubAgentConfig, agent_name: str) -> AgentResult:
            msg = IncomingMessage(
                channel="sub_agent",
                user_id=f"agent:{agent_name}",
                text=config.task,
                metadata={
                    "agent_type": config.agent_type.value,
                    "parent_agent": agent_name,
                    "max_iterations": config.max_iterations,
                    "depth": config.depth,
                },
            )
            response = await mock_handle_message(msg)
            return AgentResult(
                response=response.text,
                success=True,
                model_used=config.model,
            )

        config = SubAgentConfig(task="do something", agent_type=AgentType.WORKER)
        result = await _agent_runner(config, "test_agent")

        assert captured_msg is not None
        assert captured_msg.channel == "sub_agent"
        assert captured_msg.user_id == "agent:test_agent"
        assert captured_msg.text == "do something"
        assert captured_msg.metadata["agent_type"] == "worker"
        assert result.success is True
        assert result.response == "done"

    @pytest.mark.asyncio
    async def test_runner_timeout_returns_error(self) -> None:
        """Timeout → AgentResult(success=False)."""

        async def slow_handle(msg):
            await asyncio.sleep(10)

        async def _agent_runner(config: SubAgentConfig, agent_name: str) -> AgentResult:
            msg = IncomingMessage(
                channel="sub_agent",
                user_id=f"agent:{agent_name}",
                text=config.task,
            )
            try:
                await asyncio.wait_for(slow_handle(msg), timeout=config.timeout_seconds)
                return AgentResult(response="ok", success=True)
            except TimeoutError:
                return AgentResult(
                    response="",
                    success=False,
                    error=f"Sub-Agent Timeout nach {config.timeout_seconds}s",
                )

        config = SubAgentConfig(task="slow task", timeout_seconds=1)
        result = await _agent_runner(config, "slow_agent")

        assert result.success is False
        assert "Timeout" in (result.error or "")


class TestDelegationUsesRunner:
    @pytest.mark.asyncio
    async def test_delegation_uses_runner(self) -> None:
        """_execute_delegation() liefert nicht-leeren String wenn Runner gesetzt."""
        from cognithor.core.delegation import DelegationEngine
        from cognithor.core.orchestrator import Orchestrator

        orch = Orchestrator.__new__(Orchestrator)
        orch._runner = None
        orch._agents = {}
        orch._max_depth = 3

        async def mock_runner(config: SubAgentConfig, agent_name: str) -> AgentResult:
            return AgentResult(response="delegated result", success=True)

        orch.set_runner(mock_runner)

        engine = DelegationEngine.__new__(DelegationEngine)
        engine._orchestrator = orch

        result = await engine._execute_delegation(
            to_agent="worker_1",
            task="do work",
            context={},
        )
        assert result == "delegated result"
