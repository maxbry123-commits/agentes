"""Tests for Gatekeeper risk ceiling (ATL Phase 6)."""

from __future__ import annotations

import pytest

from cognithor.core.gatekeeper import Gatekeeper, GateStatus
from cognithor.models import PlannedAction, RiskLevel, SessionContext


@pytest.fixture
def gk():
    from cognithor.config import CognithorConfig

    return Gatekeeper(CognithorConfig())


@pytest.fixture
def ctx():
    return SessionContext(user_id="test", session_id="s1")


def _action(tool: str, params: dict | None = None) -> PlannedAction:
    return PlannedAction(tool=tool, params=params or {}, rationale="test")


def test_risk_ceiling_blocks_orange_with_yellow_ceiling(gk, ctx):
    """An ORANGE tool (http_request) should be BLOCKED when ceiling is YELLOW."""
    decision = gk.evaluate(_action("http_request"), ctx, risk_ceiling="YELLOW")
    assert decision.status == GateStatus.BLOCK
    assert "Risk-Ceiling" in decision.reason


def test_risk_ceiling_allows_green_with_yellow_ceiling(gk, ctx):
    """A GREEN tool (search_memory) should pass when ceiling is YELLOW."""
    decision = gk.evaluate(_action("search_memory"), ctx, risk_ceiling="YELLOW")
    assert decision.status != GateStatus.BLOCK


def test_risk_ceiling_allows_yellow_with_yellow_ceiling(gk, ctx):
    """A YELLOW tool (save_to_memory) should pass when ceiling is YELLOW."""
    decision = gk.evaluate(_action("save_to_memory"), ctx, risk_ceiling="YELLOW")
    assert decision.status != GateStatus.BLOCK


def test_risk_ceiling_blocks_yellow_with_green_ceiling(gk, ctx):
    """A YELLOW tool should be BLOCKED when ceiling is GREEN."""
    decision = gk.evaluate(_action("save_to_memory"), ctx, risk_ceiling="GREEN")
    assert decision.status == GateStatus.BLOCK


def test_no_ceiling_unchanged(gk, ctx):
    """Without ceiling, ORANGE tools should be ORANGE (not blocked)."""
    decision = gk.evaluate(_action("http_request"), ctx)
    assert decision.risk_level == RiskLevel.ORANGE
    assert decision.status != GateStatus.BLOCK


def test_atl_tools_classified(gk, ctx):
    """ATL tools should be properly classified."""
    # atl_status = GREEN
    d1 = gk.evaluate(_action("atl_status"), ctx)
    assert d1.risk_level == RiskLevel.GREEN

    # atl_journal = GREEN
    d2 = gk.evaluate(_action("atl_journal"), ctx)
    assert d2.risk_level == RiskLevel.GREEN

    # atl_goals = YELLOW
    d3 = gk.evaluate(_action("atl_goals"), ctx)
    assert d3.risk_level == RiskLevel.YELLOW
