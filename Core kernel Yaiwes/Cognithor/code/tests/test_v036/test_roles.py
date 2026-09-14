"""Tests for Feature 1: Create / Operate / Live Role System."""

from __future__ import annotations

import sys

import pytest

from cognithor.core.agent_router import AgentProfile
from cognithor.core.roles import (
    AgentSpawnError,
    WriteBlockedError,
    can_spawn,
    get_behaviour,
    is_tool_allowed_for_role,
    should_log_output,
    uses_extended_thinking,
)


class TestDefaultRole:
    def test_default_role_is_worker(self):
        """Load an agent profile without role field — must default to worker."""
        profile = AgentProfile(name="legacy-agent")
        assert profile.role == "worker"

    def test_old_config_loads_without_error(self):
        """AgentProfile from v0.35.6 (no role field) loads without error."""
        profile = AgentProfile(
            name="jarvis",
            display_name="Jarvis",
            description="Generalist",
            trigger_patterns=[],
        )
        assert profile.role == "worker"
        assert profile.name == "jarvis"


class TestRoleBehaviours:
    def test_all_roles_have_behaviours(self):
        for role in ("orchestrator", "worker", "monitor"):
            b = get_behaviour(role)
            assert "extended_thinking" in b
            assert "log_output" in b
            assert "available_tool_tiers" in b
            assert "can_spawn_agents" in b

    def test_orchestrator_thinking_not_logged(self):
        """Orchestrator: Extended Thinking ON, output NOT logged."""
        assert uses_extended_thinking("orchestrator") is True
        assert should_log_output("orchestrator") is False

    def test_worker_logged_no_thinking(self):
        """Worker: Extended Thinking OFF, everything logged."""
        assert uses_extended_thinking("worker") is False
        assert should_log_output("worker") is True

    def test_monitor_logged_no_thinking(self):
        """Monitor: Read-only, logged, no thinking."""
        assert uses_extended_thinking("monitor") is False
        assert should_log_output("monitor") is True


class TestSpawning:
    def test_orchestrator_can_spawn(self):
        assert can_spawn("orchestrator") is True

    def test_worker_cannot_spawn(self):
        assert can_spawn("worker") is False

    def test_monitor_cannot_spawn(self):
        assert can_spawn("monitor") is False


class TestMonitorReadOnly:
    def test_monitor_read_tools_allowed(self):
        """Monitor can use read-only tools."""
        for tool in ["read_file", "search_memory", "web_search", "git_status"]:
            assert is_tool_allowed_for_role(tool, "monitor"), f"{tool} should be allowed"

    def test_monitor_write_tools_blocked(self):
        """Monitor cannot use write tools."""
        for tool in ["write_file", "exec_command", "save_to_memory", "git_commit"]:
            assert not is_tool_allowed_for_role(tool, "monitor"), f"{tool} should be blocked"

    def test_worker_all_tools_allowed(self):
        """Worker can use any tool."""
        for tool in ["write_file", "exec_command", "read_file"]:
            assert is_tool_allowed_for_role(tool, "worker") is True

    def test_orchestrator_all_tools_allowed(self):
        """Orchestrator can use any tool."""
        for tool in ["write_file", "exec_command", "read_file"]:
            assert is_tool_allowed_for_role(tool, "orchestrator") is True


class TestExceptions:
    def test_agent_spawn_error(self):
        with pytest.raises(AgentSpawnError):
            raise AgentSpawnError("Worker cannot spawn agents")

    def test_write_blocked_error(self):
        with pytest.raises(WriteBlockedError):
            raise WriteBlockedError("Monitor cannot write")


@pytest.mark.parametrize("role", ["orchestrator", "worker", "monitor"])
class TestAllPlatforms:
    def test_role_on_current_platform(self, role):
        """All three roles work on the current platform."""
        profile = AgentProfile(name=f"test-{role}", role=role)
        assert profile.role == role
        b = get_behaviour(role)
        assert isinstance(b, dict)
        assert sys.platform in ("win32", "darwin", "linux")
