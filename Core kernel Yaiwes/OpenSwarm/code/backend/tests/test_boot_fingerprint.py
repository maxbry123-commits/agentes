"""What the client pool's boot fingerprint does and does NOT hash.

Reuse is gated on this hash, so anything the CLI subprocess freezes at boot must be in it (a stale
live client is the bug it exists to prevent), and anything sent per query must be out of it (hashing
those respawns the CLI for nothing, which is exactly what the compaction cutoff used to do)."""

import pytest

from backend.apps.agents.core.models import AgentSession
from backend.apps.agents.manager.run.client_pool import boot_fingerprint

BASE_KWARGS = {
    "model": "haiku",
    "cwd": "/tmp/ws",
    "system_prompt": {"type": "preset", "preset": "claude_code"},
    "allowed_tools": ["Read"],
    "disallowed_tools": ["mcp__claude_ai_*"],
    "mcp_servers": {"openswarm-mcp-meta": {"command": "python", "args": ["m.py"], "type": "stdio"}},
    "can_use_tool": lambda: None,
    "stderr": lambda line: None,
    "hooks": {"PreToolUse": []},
}


def make_session() -> AgentSession:
    return AgentSession(name="t", model="haiku", mode="agent")


def test_fingerprint_stable_across_per_turn_keys():
    s = make_session()
    a = boot_fingerprint(dict(BASE_KWARGS), s)
    changed = dict(BASE_KWARGS)
    changed["can_use_tool"] = lambda: 1
    changed["stderr"] = lambda line: 1
    changed["hooks"] = {"PreToolUse": ["different"]}
    changed["resume"] = "sdk-session-xyz"
    changed["fork_session"] = True
    assert boot_fingerprint(changed, s) == a


def test_fingerprint_ignores_the_compaction_cutoff():
    """The cutoff only rewrites prompt_content, which is sent per query and never frozen at boot,
    and every path that rebuilds history already forces a respawn. Hashing it respawned the CLI on
    every turn past compact_threshold_pct for zero token saving (+1.0s TTFT per turn, measured)."""
    s = make_session()
    before = boot_fingerprint(dict(BASE_KWARGS), s)
    for cutoff in ("msg42", "msg43", "msg44"):
        s.compacted_through_msg_id = cutoff
        assert boot_fingerprint(dict(BASE_KWARGS), s) == before


@pytest.mark.parametrize("mutate", [
    lambda k, s: k.__setitem__("mcp_servers", {**k["mcp_servers"], "x": {"command": "node", "type": "stdio"}}),
    lambda k, s: k.__setitem__("system_prompt", {"type": "preset", "preset": "claude_code", "append": "sel"}),
    lambda k, s: k.__setitem__("model", "gpt-5-mini"),
    lambda k, s: k.__setitem__("cwd", "/tmp/other"),
    lambda k, s: k.__setitem__("allowed_tools", ["Read", "Bash"]),
    lambda k, s: k.__setitem__("tools", ["Read", "Bash", "ToolSearch"]),
    lambda k, s: setattr(s, "active_branch_id", "branch2"),
])
def test_fingerprint_changes_on_boot_inputs(mutate):
    s = make_session()
    kwargs = dict(BASE_KWARGS)
    kwargs["mcp_servers"] = dict(BASE_KWARGS["mcp_servers"])
    before = boot_fingerprint(kwargs, s)
    mutate(kwargs, s)
    assert boot_fingerprint(kwargs, s) != before
