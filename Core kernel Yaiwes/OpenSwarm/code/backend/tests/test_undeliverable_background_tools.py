"""Never advertise a tool whose payload we cannot deliver.

Monitor and friends are background event-stream tools: the agent arms one, keeps working, and the
notification is supposed to arrive between turns. We drive the CLI strictly one turn at a time and
stop reading at the ResultMessage, so nothing ever consumes that event. The observed failure is a
user watching an agent say "I'll report back the second it's done, no need to wait around" and then
never hearing anything again.

Pruning them from the tool manifest was not enough: that has a kill switch, and flipping it handed
the model the same undeliverable promise. The deny has to live where no flag can lift it.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_undeliverable_background_tools.py -v
"""

from __future__ import annotations

from backend.apps.agents.core.models import AgentSession
from backend.apps.agents.manager.permissions import path_gate
from backend.apps.agents.manager.permissions.build_effective_tool_lists import (
    build_effective_tool_lists,
)


def p_build(allowed=None, builtin_perms=None):
    session = AgentSession(
        id="s1", name="t", model="sonnet", mode="agent",
        allowed_tools=allowed if allowed is not None else ["Read", "Bash", "Monitor"],
    )
    return build_effective_tool_lists(
        session=session,
        mcp_servers={},
        builtin_perms=builtin_perms or {},
        need_web_mcp=False,
        browser_delegation_tools=[],
        invoke_agent_tools=[],
    )


def p_disallowed(**kwargs) -> list:
    return p_build(kwargs.get("allowed_tools"), kwargs.get("builtin_perms"))[1]


def test_every_undeliverable_tool_is_withheld():
    disallowed = p_disallowed()
    for name in path_gate.UNDELIVERABLE_BACKGROUND_TOOLS:
        assert name in disallowed, f"{name} promises a between-turn callback we never deliver"


def test_monitor_specifically_cannot_be_reached():
    """The one a real user hit. Named on its own so a future edit to the tuple cannot quietly drop it."""
    assert "Monitor" in path_gate.UNDELIVERABLE_BACKGROUND_TOOLS
    assert "Monitor" in p_disallowed()


def test_withheld_even_when_explicitly_allowed():
    """A saved permission set or the manifest kill switch must not be able to hand it back."""
    disallowed = p_disallowed(
        allowed_tools=["Monitor", "PushNotification"],
        builtin_perms={"Monitor": "always_allow", "PushNotification": "always_allow"},
    )
    assert "Monitor" in disallowed
    assert "PushNotification" in disallowed


def test_ordinary_tools_are_untouched():
    """The discriminating half: this must withhold exactly these, not quietly narrow the surface."""
    allowed, disallowed = p_build(["Read", "Bash", "Glob"])
    assert "Read" in allowed and "Bash" in allowed and "Glob" in allowed
    for name in ("Read", "Bash", "Glob"):
        assert name not in disallowed


def test_no_duplicates_when_already_denied():
    disallowed = p_disallowed(builtin_perms={"Monitor": "deny"})
    assert disallowed.count("Monitor") == 1
