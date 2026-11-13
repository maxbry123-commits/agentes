"""REGRESSION — 0.83 Reddit-tools ORANGE blocking.

When Reddit tools were added in v0.83.0, they weren't added to any
classification list, so they defaulted to ORANGE — blocking every
Reddit operation with an approval prompt.

Fixed in 0.84.0: reddit_scan/reddit_leads → GREEN, reddit_reply → YELLOW.
"""

from __future__ import annotations

import pytest

from cognithor.core.gatekeeper import Gatekeeper
from cognithor.models import RiskLevel

from .conftest import make_action, make_session

pytestmark = pytest.mark.security_contract


@pytest.fixture
def gatekeeper(security_config):
    gk = Gatekeeper(security_config)
    gk.initialize()
    gk._capability_matrix = None
    return gk


@pytest.fixture
def session():
    return make_session()


# ---------------------------------------------------------------------------
# REG-083.1 — reddit_scan is GREEN
# ---------------------------------------------------------------------------


def test_reddit_scan_is_green(gatekeeper, session):
    """reddit_scan must be GREEN (read-only scanning)."""
    action = make_action("reddit_scan")
    decision = gatekeeper.evaluate(action, session)
    assert decision.risk_level == RiskLevel.GREEN, (
        f"REGRESSION: reddit_scan classified as {decision.risk_level}, expected GREEN"
    )


# ---------------------------------------------------------------------------
# REG-083.2 — reddit_leads is GREEN
# ---------------------------------------------------------------------------


def test_reddit_leads_is_green(gatekeeper, session):
    """reddit_leads must be GREEN (read-only lead listing)."""
    action = make_action("reddit_leads")
    decision = gatekeeper.evaluate(action, session)
    assert decision.risk_level == RiskLevel.GREEN, (
        f"REGRESSION: reddit_leads classified as {decision.risk_level}, expected GREEN"
    )


# ---------------------------------------------------------------------------
# REG-083.3 — reddit_reply is YELLOW
# ---------------------------------------------------------------------------


def test_reddit_reply_is_yellow(gatekeeper, session):
    """reddit_reply must be YELLOW (write action, but user is informed)."""
    action = make_action("reddit_reply")
    decision = gatekeeper.evaluate(action, session)
    assert decision.risk_level == RiskLevel.YELLOW, (
        f"REGRESSION: reddit_reply classified as {decision.risk_level}, expected YELLOW"
    )


# ---------------------------------------------------------------------------
# REG-083.4 — reddit_refine is GREEN
# ---------------------------------------------------------------------------


def test_reddit_refine_is_green(gatekeeper, session):
    """reddit_refine must be GREEN (read-only refinement)."""
    action = make_action("reddit_refine")
    decision = gatekeeper.evaluate(action, session)
    assert decision.risk_level == RiskLevel.GREEN, (
        f"REGRESSION: reddit_refine classified as {decision.risk_level}, expected GREEN"
    )
