"""INVARIANT 6 — Risk classification is consistent across entry points.

The same tool call reaching the Gatekeeper via any channel MUST receive
the same classification. No channel can upgrade or downgrade risk.
"""

from __future__ import annotations

import pytest

from cognithor.core.gatekeeper import Gatekeeper
from cognithor.models import GateStatus, RiskLevel

from .conftest import make_action, make_session

pytestmark = pytest.mark.security_contract

CHANNELS = [
    "cli",
    "telegram",
    "discord",
    "slack",
    "whatsapp",
    "signal",
    "matrix",
    "irc",
    "mattermost",
    "teams",
    "google_chat",
    "feishu",
    "imessage",
    "twitch",
    "webui",
    "voice",
    "api",
]

REPRESENTATIVE_TOOLS = {
    "read_file": RiskLevel.GREEN,
    "save_to_memory": RiskLevel.YELLOW,
    "email_send": RiskLevel.ORANGE,
    "vault_delete": RiskLevel.RED,
}


@pytest.fixture
def gatekeeper(security_config):
    gk = Gatekeeper(security_config)
    gk.initialize()
    gk._capability_matrix = None
    return gk


# ---------------------------------------------------------------------------
# INV-6.1 — _classify_risk has no channel parameter
# ---------------------------------------------------------------------------


def test_classify_risk_has_no_channel_param(gatekeeper):
    """_classify_risk signature must not accept a channel parameter."""
    import inspect

    sig = inspect.signature(gatekeeper._classify_risk)
    param_names = set(sig.parameters.keys())
    assert "channel" not in param_names
    assert "channel_name" not in param_names


# ---------------------------------------------------------------------------
# INV-6.2 — Same tool, same risk, all channels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("tool,expected_risk", list(REPRESENTATIVE_TOOLS.items()))
def test_same_tool_same_risk_all_channels(tool, expected_risk, channel, gatekeeper):
    """Same tool must get same risk regardless of channel in context."""
    session = make_session(channel=channel)
    action = make_action(tool)
    decision = gatekeeper.evaluate(action, session)
    assert decision.risk_level == expected_risk, (
        f"Tool '{tool}' got {decision.risk_level} via channel '{channel}', expected {expected_risk}"
    )


# ---------------------------------------------------------------------------
# INV-6.3 — Identical contexts differing only in channel
# ---------------------------------------------------------------------------


def test_evaluate_ignores_session_channel(gatekeeper):
    """Two sessions differing only in channel field must yield identical decisions."""
    action = make_action("delete_file")
    session_cli = make_session(channel="cli")
    session_tg = make_session(channel="telegram")

    d_cli = gatekeeper.evaluate(action, session_cli)
    d_tg = gatekeeper.evaluate(action, session_tg)

    assert d_cli.status == d_tg.status
    assert d_cli.risk_level == d_tg.risk_level


# ---------------------------------------------------------------------------
# INV-6.4 — Cron-triggered same as user
# ---------------------------------------------------------------------------


def test_cron_triggered_same_as_user(gatekeeper):
    """A cron-originated action must get the same classification."""
    action = make_action("email_send")
    user_session = make_session(channel="cli")
    cron_session = make_session(channel="cron")

    d_user = gatekeeper.evaluate(action, user_session)
    d_cron = gatekeeper.evaluate(action, cron_session)

    assert d_user.risk_level == d_cron.risk_level


# ---------------------------------------------------------------------------
# INV-6.5 — Kanban-triggered same as user
# ---------------------------------------------------------------------------


def test_kanban_triggered_same_as_user(gatekeeper):
    """A kanban-originated action must get the same classification."""
    action = make_action("remote_exec")
    user_session = make_session(channel="cli")
    kanban_session = make_session(channel="kanban")

    d_user = gatekeeper.evaluate(action, user_session)
    d_kanban = gatekeeper.evaluate(action, kanban_session)

    assert d_user.risk_level == d_kanban.risk_level


# ---------------------------------------------------------------------------
# INV-6.6 — Risk ceiling is per-context, not per-channel
# ---------------------------------------------------------------------------


def test_risk_ceiling_applies_same_regardless_of_channel(gatekeeper):
    """risk_ceiling must restrict identically across channels."""
    action = make_action("email_send")

    for ch in ["cli", "telegram", "webui"]:
        session = make_session(channel=ch)
        decision = gatekeeper.evaluate(action, session, risk_ceiling="YELLOW")
        assert decision.status == GateStatus.BLOCK, (
            f"risk_ceiling=YELLOW should BLOCK ORANGE tool via {ch}"
        )


# ---------------------------------------------------------------------------
# INV-6.7 — API channel no privilege escalation
# ---------------------------------------------------------------------------


def test_api_channel_no_privilege_escalation(gatekeeper):
    """API channel must not bypass any classification that CLI enforces."""
    tools_to_check = ["email_send", "vault_delete", "delete_file", "read_file"]

    for tool in tools_to_check:
        action = make_action(tool)
        d_cli = gatekeeper.evaluate(action, make_session(channel="cli"))
        d_api = gatekeeper.evaluate(action, make_session(channel="api"))

        assert d_cli.risk_level == d_api.risk_level, (
            f"Tool '{tool}': CLI={d_cli.risk_level}, API={d_api.risk_level}"
        )
        assert d_cli.status == d_api.status
