"""Security Contract Test Suite — Shared Fixtures.

These tests verify security INVARIANTS, not features.
The Gatekeeper, AuditTrail, ToolEnforcer, and AST guards are
always the REAL implementations — only their dependencies are mocked.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pytest

from cognithor.config import CognithorConfig
from cognithor.models import (
    AuditEntry,
    GateStatus,
    PlannedAction,
    RiskLevel,
    SessionContext,
)
from cognithor.security.audit import AuditTrail

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def make_action(tool: str, params: dict[str, Any] | None = None, **kw: Any) -> PlannedAction:
    return PlannedAction(tool=tool, params=params or {}, **kw)


def make_audit_entry(
    tool: str = "read_file",
    status: GateStatus = GateStatus.ALLOW,
    risk: RiskLevel = RiskLevel.GREEN,
    session_id: str = "test-session",
    **kw: Any,
) -> AuditEntry:
    params_hash = hashlib.sha256(b"test").hexdigest()
    return AuditEntry(
        session_id=session_id,
        action_tool=tool,
        action_params_hash=params_hash,
        decision_status=status,
        decision_reason=kw.pop("reason", "test"),
        risk_level=risk,
        **kw,
    )


def make_session(channel: str = "cli", **kw: Any) -> SessionContext:
    return SessionContext(channel=channel, **kw)


# ---------------------------------------------------------------------------
# Fake channel for HITL tests
# ---------------------------------------------------------------------------


@dataclass
class ApprovalRequest:
    session_id: str
    tool: str
    reason: str


@dataclass
class FakeChannel:
    """Channel with programmable approval responses."""

    approval_responses: dict[str, bool] = field(default_factory=dict)
    default_response: bool | None = None
    should_timeout: bool = False
    should_raise: bool = False
    requests: list[ApprovalRequest] = field(default_factory=list)

    async def request_approval(
        self,
        session_id: str,
        action: Any = None,
        reason: str = "",
        **_kw: Any,
    ) -> bool:
        tool = getattr(action, "tool", "") if action else ""
        self.requests.append(ApprovalRequest(session_id, tool, reason))
        if self.should_raise:
            raise ConnectionError("channel down")
        if self.should_timeout:
            raise TimeoutError()
        if tool in self.approval_responses:
            return self.approval_responses[tool]
        if self.default_response is not None:
            return self.default_response
        return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def security_config(tmp_path: Path) -> CognithorConfig:
    home = tmp_path / ".cognithor"
    return CognithorConfig(cognithor_home=home)


@pytest.fixture
def audit_trail(tmp_path: Path) -> AuditTrail:
    return AuditTrail(log_path=tmp_path / "audit.jsonl")


@pytest.fixture
def audit_log_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture
def fake_channel() -> FakeChannel:
    return FakeChannel()
