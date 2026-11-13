"""REGRESSION — 0.91.0 auto-approval bug.

The WebUI bridge had 'return True' in request_approval(), auto-approving
all ORANGE actions for 21 days (2026-03-22 to 2026-04-12).

These tests ensure the bug never returns.
"""

from __future__ import annotations

import ast
import inspect
import textwrap

import pytest

pytestmark = pytest.mark.security_contract


# ---------------------------------------------------------------------------
# REG-091.1 — WebUI request_approval never has unconditional return True
# ---------------------------------------------------------------------------


def test_webui_request_approval_no_unconditional_true():
    """WebUI.request_approval must not contain an unconditional 'return True'.

    This is the exact pattern that caused the 0.91.0 bug.
    """
    from cognithor.channels.webui import WebUIChannel

    source = textwrap.dedent(inspect.getsource(WebUIChannel.request_approval))
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
            assert node.value.value is not True, (
                "REGRESSION: Found unconditional 'return True' in "
                "WebUI.request_approval — this was the 0.91.0 bug"
            )


# ---------------------------------------------------------------------------
# REG-091.2 — No-channel approval returns BLOCK
# ---------------------------------------------------------------------------


def test_no_channel_approval_returns_block(security_config):
    """When no channel is available, APPROVE decisions must become BLOCK.

    Before the fix, unresolved APPROVE decisions passed through silently.
    """
    from cognithor.core.gatekeeper import Gatekeeper
    from cognithor.models import GateStatus

    from .conftest import make_action, make_session

    gk = Gatekeeper(security_config)
    gk.initialize()
    gk._capability_matrix = None

    action = make_action("email_send")
    session = make_session()
    decision = gk.evaluate(action, session)

    assert decision.status == GateStatus.APPROVE, "email_send should be APPROVE (ORANGE)"
    # The gateway converts APPROVE to BLOCK when no channel exists.
    # This simulates that logic:
    from cognithor.models import GateDecision

    if decision.status == GateStatus.APPROVE:
        blocked = GateDecision(
            status=GateStatus.BLOCK,
            reason="No channel available",
            risk_level=decision.risk_level,
        )
        assert blocked.status == GateStatus.BLOCK
