"""Headless gating: the tools that dead-end must be gone from the effective tool surface, and an
'ask' must deny on the spot instead of parking on the 600s approval timeout. Two gates, not one:
ShowUI/AskUI and AskUserQuestion need a person, so OPENSWARM_HEADLESS=1 alone kills them, while
browser/app delegation only needs a window, so a headless box that boots one (the cloud runner
under Xvfb) keeps them. Every case is paired with its twin, because a gate that can't be seen
switching off proves nothing."""

import pytest
from unittest.mock import AsyncMock, patch

from backend.apps.agents.core.models import AgentSession
from backend.apps.agents.manager.permissions import workflow_approval
from backend.apps.agents.manager.permissions.build_effective_tool_lists import build_effective_tool_lists
from backend.apps.agents.manager.register_builtin_mcp_servers import register_builtin_mcp_servers
from backend.apps.agents.manager.streaming.HookContext import HookContext
from backend.apps.agents.core.ws_manager import ws_manager
from backend.config.headless import HUMAN_BOUND_TOOLS, RENDERER_BOUND_TOOLS, denied_tools

BROWSER_DELEGATION = ("CreateBrowserAgent", "BrowserAgent", "BrowserAgents", "AppAgent")


def p_session():
    session = AgentSession(name="t", model="sonnet", dashboard_id="d")
    session.allowed_tools = ["Read", "Bash", "AskUserQuestion"]
    return session


def p_run_the_real_pipeline():
    """Registration then tool-list build, in the order the agent loop runs them."""
    session = p_session()
    mcp_servers = {}
    browser_tools, invoke_tools = register_builtin_mcp_servers(
        mcp_servers, session, {}, None, None)
    allowed, disallowed = build_effective_tool_lists(
        session, mcp_servers, {}, False, browser_tools, invoke_tools)
    return mcp_servers, allowed, disallowed


def p_ctx() -> HookContext:
    session = p_session()
    return HookContext(
        session=session,
        session_id=session.id,
        prompt="hi",
        builtin_perms={},
        policy_defaults={},
        sessions={},
    )


@pytest.fixture
def no_renderer(monkeypatch):
    """No window has ever attached, the state a container starts in."""
    monkeypatch.setattr(ws_manager, "renderer_ever_attached", False, raising=False)


@pytest.fixture
def renderer_attached(monkeypatch):
    """A window registered on the dashboard socket, the state the runner waits for."""
    monkeypatch.setattr(ws_manager, "renderer_ever_attached", True, raising=False)


def test_the_two_denied_sets_split_by_what_they_actually_need():
    assert RENDERER_BOUND_TOOLS == frozenset(BROWSER_DELEGATION)
    assert HUMAN_BOUND_TOOLS == frozenset({"ShowUI", "AskUserQuestion"})


def test_a_renderer_buys_back_the_browser_tools_but_never_the_human_ones(monkeypatch, renderer_attached):
    monkeypatch.setenv("OPENSWARM_HEADLESS", "1")
    assert denied_tools() == HUMAN_BOUND_TOOLS


def test_a_desktop_launch_denies_nothing_even_before_its_window_loads(monkeypatch, no_renderer):
    monkeypatch.delenv("OPENSWARM_HEADLESS", raising=False)
    assert denied_tools() == frozenset()


def test_headless_with_a_renderer_offers_the_browser_server_again(monkeypatch, renderer_attached):
    monkeypatch.setenv("OPENSWARM_HEADLESS", "1")
    mcp_servers, allowed, disallowed = p_run_the_real_pipeline()
    assert "browser" in mcp_servers["openswarm-core"]["env"]["OSW_MCP_MODULES"].split(",")
    for tool in BROWSER_DELEGATION:
        assert f"mcp__openswarm-core__{tool}" in allowed
    # Still nobody to answer, so the human-bound pair stays gone.
    assert "ui" not in mcp_servers["openswarm-core"]["env"]["OSW_MCP_MODULES"].split(",")
    assert "AskUserQuestion" in disallowed


def test_headless_drops_the_renderer_bound_servers_and_tools(monkeypatch, no_renderer):
    monkeypatch.setenv("OPENSWARM_HEADLESS", "1")
    mcp_servers, allowed, disallowed = p_run_the_real_pipeline()
    assert "browser" not in mcp_servers["openswarm-core"]["env"]["OSW_MCP_MODULES"].split(",")
    assert "ui" not in mcp_servers["openswarm-core"]["env"]["OSW_MCP_MODULES"].split(",")
    for tool in BROWSER_DELEGATION:
        assert f"mcp__openswarm-core__{tool}" not in allowed
    for ui_tool in ("ShowUI", "AskUI"):
        assert f"mcp__openswarm-core__{ui_tool}" not in allowed
    assert "AskUserQuestion" not in allowed
    assert "AskUserQuestion" in disallowed
    # The rest of the surface is untouched; headless prunes the renderer, it doesn't lobotomise the agent.
    assert "Read" in allowed and "Bash" in allowed
    assert "invoke" in mcp_servers["openswarm-core"]["env"]["OSW_MCP_MODULES"].split(",")
    assert "openswarm-core" in mcp_servers


def test_without_headless_every_one_of_them_is_offered(monkeypatch, no_renderer):
    monkeypatch.delenv("OPENSWARM_HEADLESS", raising=False)
    mcp_servers, allowed, _ = p_run_the_real_pipeline()
    assert "browser" in mcp_servers["openswarm-core"]["env"]["OSW_MCP_MODULES"].split(",")
    assert "ui" in mcp_servers["openswarm-core"]["env"]["OSW_MCP_MODULES"].split(",")
    for tool in BROWSER_DELEGATION:
        assert f"mcp__openswarm-core__{tool}" in allowed
    for ui_tool in ("ShowUI", "AskUI"):
        assert f"mcp__openswarm-core__{ui_tool}" in allowed


def test_askuserquestion_survives_when_the_ui_server_is_absent(monkeypatch):
    # With no openswarm-ui registered nothing else denies AskUserQuestion, so this isolates the headless gate.
    monkeypatch.delenv("OPENSWARM_HEADLESS", raising=False)
    allowed, disallowed = build_effective_tool_lists(p_session(), {}, {}, False, [], [])
    assert "AskUserQuestion" in allowed and "AskUserQuestion" not in disallowed
    monkeypatch.setenv("OPENSWARM_HEADLESS", "1")
    allowed, disallowed = build_effective_tool_lists(p_session(), {}, {}, False, [], [])
    assert "AskUserQuestion" not in allowed and "AskUserQuestion" in disallowed


def test_only_the_exact_flag_value_turns_headless_on(monkeypatch, no_renderer):
    monkeypatch.setenv("OPENSWARM_HEADLESS", "0")
    _, allowed, _ = p_run_the_real_pipeline()
    assert "mcp__openswarm-core__ShowUI" in allowed


@pytest.mark.asyncio
async def test_headless_denies_an_ask_without_ever_prompting(monkeypatch):
    monkeypatch.setenv("OPENSWARM_HEADLESS", "1")
    ask = AsyncMock()
    with patch.object(workflow_approval, "request_user_approval", new=ask):
        decision = await workflow_approval.resolve_ask(p_ctx(), "Bash", {"command": "ls"}, None)
    assert decision.behavior == "deny"
    assert not ask.called  # never broadcast into the void, so never a 600s park


@pytest.mark.asyncio
async def test_without_headless_an_ask_still_prompts(monkeypatch):
    monkeypatch.delenv("OPENSWARM_HEADLESS", raising=False)
    ask = AsyncMock(return_value=workflow_approval.ApprovalDecision(behavior="allow"))
    with patch.object(workflow_approval, "request_user_approval", new=ask):
        decision = await workflow_approval.resolve_ask(p_ctx(), "Bash", {"command": "ls"}, None)
    assert decision.behavior == "allow"
    assert ask.called


@pytest.mark.asyncio
async def test_headless_still_honors_a_remembered_allow(monkeypatch):
    monkeypatch.setenv("OPENSWARM_HEADLESS", "1")
    ctx = p_ctx()
    workflow_approval.set_workflow_approval_memory(
        ctx.session_id, decisions={"Bash": "allow"}, step_usage={}, remember=None, ask_timeout=5.0)
    try:
        decision = await workflow_approval.resolve_ask(ctx, "Bash", {"command": "ls"}, None)
    finally:
        workflow_approval.clear_workflow_approval_memory(ctx.session_id)
    assert decision.behavior == "allow"
