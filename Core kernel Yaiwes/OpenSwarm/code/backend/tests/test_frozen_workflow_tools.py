"""A workflow's frozen Actions set has to actually restrict the run.

It did not. `AgentConfig.allowed_tools` was computed by the executor, passed to launch, and then
dropped on the floor: launch resolved tools purely from the mode. So the Actions page offered a
permission toggle that no dispatch code read, which is worse than offering nothing, because it
sells a boundary that is not there. An unattended 3am run with Bash and nobody to deny an approval
is exactly the case the toggle exists for.

None still means "whatever the mode allows", so an unfrozen workflow keeps the full surface.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_frozen_workflow_tools.py -v
"""

from __future__ import annotations

from typing import List

from backend.apps.agents.core.models import AgentConfig
from backend.apps.agents.manager.AgentLaunch import resolve_launch_tools


def p_resolve(config: AgentConfig, mode_tools: List[str]) -> List[str]:
    """Drives the REAL launch-time resolver, not a copy of it. A mirrored implementation here would
    keep passing even if launch went back to ignoring the frozen set entirely."""
    return resolve_launch_tools(mode_tools, config.allowed_tools)


P_MODE = ["Read", "Edit", "Write", "Bash", "Glob", "Grep", "WebSearch", "AskUserQuestion"]


def test_default_is_unrestricted():
    """Every normal chat posts a config with no allowed_tools. If the default were a list instead of
    None, honouring it would silently strip the whole app down to that list."""
    assert AgentConfig(name="chat").allowed_tools is None


def test_unfrozen_workflow_keeps_the_full_mode_surface():
    assert p_resolve(AgentConfig(name="wf"), P_MODE) == P_MODE


def test_frozen_set_actually_removes_tools():
    config = AgentConfig(name="wf", allowed_tools=["Read", "Glob"])
    resolved = p_resolve(config, P_MODE)
    assert resolved == ["Read", "Glob"]
    assert "Bash" not in resolved, "the whole point: a frozen set must be able to withhold Bash"
    assert "Write" not in resolved


def test_a_frozen_set_cannot_widen_the_mode():
    """Intersect, never trust. A stale saved set naming a tool the mode does not grant must not
    smuggle it back in."""
    config = AgentConfig(name="wf", allowed_tools=["Read", "NotebookEdit", "BrowserClick"])
    resolved = p_resolve(config, ["Read", "Bash"])
    assert resolved == ["Read"]


def test_an_explicitly_empty_set_grants_nothing():
    """Distinct from None on purpose. This is why the workflow edit and scheduling chats had to move
    off [] and onto None: under the old dead code [] was harmless, now it means zero tools."""
    assert p_resolve(AgentConfig(name="wf", allowed_tools=[]), P_MODE) == []


def test_order_follows_the_mode_not_the_saved_set():
    config = AgentConfig(name="wf", allowed_tools=["Grep", "Read"])
    assert p_resolve(config, P_MODE) == ["Read", "Grep"]


def test_workflow_call_sites_do_not_pass_an_empty_list():
    """Guards the migration: an [] left behind at any AgentConfig site is now a silently toolless
    agent, which reads to the user as the agent being broken."""
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for rel in ("apps/workflows/workflows.py", "apps/workflows/executor.py"):
        src = (root / rel).read_text()
        assert not re.search(r"allowed_tools=\[\]", src), f"{rel} still passes an empty allowed_tools"
