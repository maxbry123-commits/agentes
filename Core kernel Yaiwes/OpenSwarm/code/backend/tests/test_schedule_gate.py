"""The always-on openswarm-schedule MCP must never fall through to always_allow:
its committing tools force an approval and Claude's internal Cron* tools are denied,
even when the user set everything to always_allow. This is the unattended-widen guard
the scheduled-tasks PR shipped without a test, and the exact path most at risk in the
agent-manager decomposition (the gating moved from agent_manager into path_gate)."""

from backend.apps.agents.manager.permissions import path_gate
from backend.apps.agents.manager.permissions.workflow_approval import is_claude_schedule_skill


def test_schedule_commit_tools_force_ask_even_when_always_allow():
    for tool in (
        "mcp__openswarm-core__ScheduleWorkflow",
        "mcp__openswarm-core__UpdateScheduledWorkflow",
        "mcp__openswarm-core__DeleteScheduledWorkflow",
        "mcp__openswarm-core__PauseAllWorkflows",
    ):
        policy, _ = path_gate.maybe_override_policy("always_allow", tool, {})
        assert policy == "ask", f"{tool} must force an approval, not silently always_allow"


def test_claude_internal_cron_tools_denied():
    for tool in ("CronCreate", "CronList", "CronDelete"):
        policy, _ = path_gate.maybe_override_policy("always_allow", tool, {})
        assert policy == "deny", f"{tool} must be denied in favour of the native scheduler"


def test_claude_schedule_skill_detected():
    assert is_claude_schedule_skill("Skill", {"skill": "schedule"})
    assert is_claude_schedule_skill("Skill", {"skill": "Schedule"})
    assert not is_claude_schedule_skill("Skill", {"skill": "other"})
    assert not is_claude_schedule_skill("Bash", {"skill": "schedule"})
    assert not is_claude_schedule_skill("Skill", "not a dict")


def test_normal_tool_unaffected_by_schedule_gate():
    policy, _ = path_gate.maybe_override_policy("always_allow", "Read", {})
    assert policy == "always_allow"
