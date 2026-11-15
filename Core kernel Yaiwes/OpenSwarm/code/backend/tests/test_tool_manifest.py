"""OSW_TOOL_MANIFEST gate: default ships an explicit FULL_TOOLS list that prunes dead preset
built-ins WITHOUT dropping anything OpenSwarm uses; OSW_TOOL_MANIFEST=0 is the kill switch back to
the full claude_code preset. The manifest MUST keep every built-in in effective_allowed's source set
+ ToolSearch (so deferred MCP loading survives); MCP tools ride mcp_servers, not this list."""


from backend.apps.agents.manager.prompt.tool_catalog import (
    FULL_TOOLS,
    resolve_builtin_tools_option,
)

PRESET = {"type": "preset", "preset": "claude_code"}


def test_default_is_the_explicit_full_tools_manifest(monkeypatch):
    monkeypatch.delenv("OSW_TOOL_MANIFEST", raising=False)
    out = resolve_builtin_tools_option()
    assert isinstance(out, list)
    assert out == list(FULL_TOOLS)
    # A fresh copy, never the module list itself (a caller mutation must not poison FULL_TOOLS).
    assert out is not FULL_TOOLS


def test_kill_switch_restores_the_full_preset(monkeypatch):
    monkeypatch.setenv("OSW_TOOL_MANIFEST", "0")
    assert resolve_builtin_tools_option() == PRESET


def test_manifest_keeps_toolsearch_so_deferred_mcp_loading_survives(monkeypatch):
    monkeypatch.delenv("OSW_TOOL_MANIFEST", raising=False)
    assert "ToolSearch" in resolve_builtin_tools_option()


def test_manifest_keeps_every_core_builtin_openswarm_exposes(monkeypatch):
    # These are the built-ins the agent actually uses; none may vanish from the manifest.
    monkeypatch.delenv("OSW_TOOL_MANIFEST", raising=False)
    out = resolve_builtin_tools_option()
    for core in ("Read", "Edit", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"):
        assert core in out


def test_manifest_drops_only_builtins_nothing_in_the_repo_references(monkeypatch):
    # Live-measured saving comes from exactly these; if one ever gains a caller, it must come back.
    monkeypatch.delenv("OSW_TOOL_MANIFEST", raising=False)
    out = resolve_builtin_tools_option()
    for dead in ("Monitor", "PushNotification", "RemoteTrigger", "ScheduleWakeup", "Skill"):
        assert dead not in out


def test_both_halves_of_a_paired_tool_ship_together(monkeypatch):
    """An Enter with no Exit strands the agent in whatever mode it entered. ExitWorktree was pruned
    as "unreferenced" while EnterWorktree stayed, which is how that gap got in."""
    monkeypatch.delenv("OSW_TOOL_MANIFEST", raising=False)
    out = resolve_builtin_tools_option()
    for enter, exit_ in (("EnterPlanMode", "ExitPlanMode"), ("EnterWorktree", "ExitWorktree")):
        assert (enter in out) == (exit_ in out), f"{enter} and {exit_} must ship together"


def test_only_the_exact_kill_switch_value_flips_it(monkeypatch):
    monkeypatch.setenv("OSW_TOOL_MANIFEST", "false")  # not "0"
    assert resolve_builtin_tools_option() == list(FULL_TOOLS)
    monkeypatch.setenv("OSW_TOOL_MANIFEST", "1")
    assert resolve_builtin_tools_option() == list(FULL_TOOLS)
