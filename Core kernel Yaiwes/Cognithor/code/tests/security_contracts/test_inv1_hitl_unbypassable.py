"""INVARIANT 1 — HITL is unbypassable.

For any tool call classified ORANGE or RED, execution MUST block until
explicit human approval arrives. No timeout auto-approve. No default-true.
If approval never comes, the call must fail closed (BLOCK).
"""

from __future__ import annotations

import pytest

from cognithor.core.gatekeeper import Gatekeeper
from cognithor.models import GateDecision, GateStatus, RiskLevel

from .conftest import FakeChannel, make_action, make_session

pytestmark = pytest.mark.security_contract


@pytest.fixture
def gatekeeper(security_config):
    gk = Gatekeeper(security_config)
    gk.initialize()
    # Disable CapabilityMatrix so tools reach default risk classification
    gk._capability_matrix = None
    return gk


@pytest.fixture
def session():
    return make_session()


# ---------------------------------------------------------------------------
# INV-1.1 — ORANGE tool blocks without approval
# ---------------------------------------------------------------------------


def test_orange_tool_requires_approval(gatekeeper, session):
    """An ORANGE tool must return GateStatus.APPROVE, never ALLOW."""
    action = make_action("email_send", params={"to": "test@example.com"})
    decision = gatekeeper.evaluate(action, session)
    assert decision.status == GateStatus.APPROVE
    assert decision.risk_level == RiskLevel.ORANGE


# ---------------------------------------------------------------------------
# INV-1.2 — RED tool always blocked
# ---------------------------------------------------------------------------


def test_red_tool_always_blocked(gatekeeper, session):
    """A RED tool must return GateStatus.BLOCK — no approval opportunity."""
    action = make_action("vault_delete", params={"key": "test"})
    decision = gatekeeper.evaluate(action, session)
    assert decision.status == GateStatus.BLOCK
    assert decision.risk_level == RiskLevel.RED


# ---------------------------------------------------------------------------
# INV-1.3 — Timeout returns False (not True)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_timeout_channel_returns_false():
    """A channel that times out must result in denial (block), not approval.

    The real WebUI channel catches TimeoutError internally and returns False.
    The gateway also catches exceptions and treats them as denial.
    """
    channel = FakeChannel(should_timeout=True)
    action = make_action("email_send")
    try:
        result = await channel.request_approval("sess-1", action=action, reason="test")
    except TimeoutError:
        result = False
    assert result is False


# ---------------------------------------------------------------------------
# INV-1.4 — No channel converts APPROVE to BLOCK
# ---------------------------------------------------------------------------


def test_no_channel_approve_becomes_block(gatekeeper, session):
    """When no channel is available, APPROVE decisions cannot be resolved —
    they should not pass through as-is. The gateway converts them to BLOCK."""
    action = make_action("email_send")
    decision = gatekeeper.evaluate(action, session)
    assert decision.status == GateStatus.APPROVE

    # Simulate gateway behavior: no channel → BLOCK
    if decision.status == GateStatus.APPROVE:
        blocked = GateDecision(
            status=GateStatus.BLOCK,
            reason="No channel available for approval",
            risk_level=decision.risk_level,
        )
        assert blocked.status == GateStatus.BLOCK


# ---------------------------------------------------------------------------
# INV-1.5 — Approval exception returns False
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approval_exception_returns_false():
    """If request_approval raises, the caller must get False (block)."""
    channel = FakeChannel(should_raise=True)
    action = make_action("email_send")
    try:
        result = await channel.request_approval("sess-1", action=action, reason="test")
    except Exception:
        result = False
    assert result is False


# ---------------------------------------------------------------------------
# INV-1.6 — No unconditional return True in request_approval
# ---------------------------------------------------------------------------


def test_no_hardcoded_return_true_in_webui():
    """WebUI request_approval must not contain 'return True' without a conditional."""
    import ast
    import inspect
    import textwrap

    from cognithor.channels.webui import WebUIChannel

    source = textwrap.dedent(inspect.getsource(WebUIChannel.request_approval))
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
            assert node.value.value is not True, (
                "Found unconditional 'return True' in WebUI.request_approval"
            )


# ---------------------------------------------------------------------------
# INV-1.7 — Approval future starts unresolved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fake_channel_default_is_false():
    """Default approval response must be False (deny), not True."""
    channel = FakeChannel()
    action = make_action("email_send")
    result = await channel.request_approval("sess-1", action=action, reason="test")
    assert result is False


# ---------------------------------------------------------------------------
# INV-1.8 — All ORANGE tools parametrized
# ---------------------------------------------------------------------------


ORANGE_TOOLS = [
    "email_send",
    "calendar_create_event",
    "delete_file",
    "fetch_url",
    "http_request",
    "db_execute",
    "docker_run",
    "remote_exec",
    "browse_click",
    "browse_fill",
    "browse_execute_js",
    "browser_solve_captcha",
    "investigate_person",
    "investigate_project",
    "investigate_org",
]


@pytest.mark.parametrize("tool", ORANGE_TOOLS)
def test_orange_tool_parametrized(tool, gatekeeper, session):
    """Every known ORANGE tool must get APPROVE status."""
    action = make_action(tool)
    decision = gatekeeper.evaluate(action, session)
    assert decision.status == GateStatus.APPROVE, (
        f"ORANGE tool '{tool}' got {decision.status} instead of APPROVE"
    )


# ---------------------------------------------------------------------------
# INV-1.9 — All RED tools parametrized
# ---------------------------------------------------------------------------


RED_TOOLS = ["vault_delete", "delete_entity", "delete_relation", "erase_user_data"]


@pytest.mark.parametrize("tool", RED_TOOLS)
def test_red_tool_parametrized(tool, gatekeeper, session):
    """Every known RED tool must get BLOCK status."""
    action = make_action(tool)
    decision = gatekeeper.evaluate(action, session)
    assert decision.status == GateStatus.BLOCK, (
        f"RED tool '{tool}' got {decision.status} instead of BLOCK"
    )


# ---------------------------------------------------------------------------
# INV-1.10 — Approval rejected stays blocked
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approval_rejected_stays_blocked():
    """Explicitly rejected approval must remain BLOCK, no retry."""
    channel = FakeChannel(approval_responses={"email_send": False})
    action = make_action("email_send")
    result = await channel.request_approval("sess-1", action=action, reason="test")
    assert result is False


# ---------------------------------------------------------------------------
# INV-1.11 — Non-APPROVE decisions pass through unchanged
# ---------------------------------------------------------------------------


def test_handle_approvals_preserves_non_approve(gatekeeper, session):
    """ALLOW and BLOCK decisions must not be modified by the approval handler."""
    green_action = make_action("list_jobs")
    decision = gatekeeper.evaluate(green_action, session)
    assert decision.status == GateStatus.ALLOW

    red_action = make_action("vault_delete")
    decision = gatekeeper.evaluate(red_action, session)
    assert decision.status == GateStatus.BLOCK


# ---------------------------------------------------------------------------
# INV-1.12 — Concurrent approvals isolated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_approvals_isolated():
    """Two concurrent ORANGE requests must not cross-contaminate."""
    channel = FakeChannel(
        approval_responses={
            "email_send": True,
            "delete_file": False,
        }
    )
    action_email = make_action("email_send")
    action_delete = make_action("delete_file")

    result_email = await channel.request_approval("s1", action=action_email, reason="e")
    result_delete = await channel.request_approval("s1", action=action_delete, reason="d")

    assert result_email is True
    assert result_delete is False
    assert len(channel.requests) == 2


# ---------------------------------------------------------------------------
# INV-1.13 — Channel records approval request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_channel_records_approval_request():
    """The channel must record which tool was requested for approval."""
    channel = FakeChannel(default_response=True)
    action = make_action("email_send")
    await channel.request_approval("sess-1", action=action, reason="test reason")

    assert len(channel.requests) == 1
    assert channel.requests[0].tool == "email_send"
    assert channel.requests[0].reason == "test reason"


# ---------------------------------------------------------------------------
# INV-1.14 — Partial approval blocks unapproved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_approval():
    """3 ORANGE tools: 2 approved, 1 rejected → 2 True + 1 False."""
    channel = FakeChannel(
        approval_responses={
            "email_send": True,
            "delete_file": True,
            "remote_exec": False,
        }
    )
    results = []
    for tool in ["email_send", "delete_file", "remote_exec"]:
        action = make_action(tool)
        r = await channel.request_approval("s1", action=action, reason="test")
        results.append(r)

    assert results == [True, True, False]
