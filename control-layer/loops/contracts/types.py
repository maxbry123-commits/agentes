"""Contratos Loop — tipos deterministas v1.
SOURCE: loop_*.schema.yaml · 0% LLM
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal

LoopStateName = Literal[
    "CREATED", "LOCKED", "RUNNING", "VALIDATING", "REPAIRING",
    "CHECKPOINT", "DECIDING", "CLOSED", "ESCALATED", "FAILED",
    "CANCELLED", "PAUSED",
]

LoopCommandName = Literal[
    "START", "CANCEL", "PAUSE", "RESUME", "RETRY",
    "ABORT", "FORCE_CHECKPOINT", "REOPEN",
]

TRANSITIONS: dict[str, frozenset[str]] = {
    "CREATED": frozenset({"LOCKED", "CANCELLED"}),
    "LOCKED": frozenset({"RUNNING", "CANCELLED"}),
    "RUNNING": frozenset({"VALIDATING", "CHECKPOINT", "PAUSED", "FAILED", "CANCELLED"}),
    "VALIDATING": frozenset({"DECIDING", "REPAIRING", "FAILED"}),
    "REPAIRING": frozenset({"RUNNING", "ESCALATED", "FAILED"}),
    "CHECKPOINT": frozenset({"RUNNING", "PAUSED", "DECIDING"}),
    "DECIDING": frozenset({"RUNNING", "CLOSED", "ESCALATED", "FAILED", "CANCELLED"}),
    "PAUSED": frozenset({"RUNNING", "CANCELLED"}),
    "CLOSED": frozenset(),
    "ESCALATED": frozenset(),
    "FAILED": frozenset(),
    "CANCELLED": frozenset(),
}

TERMINAL = frozenset({"CLOSED", "ESCALATED", "FAILED", "CANCELLED"})


@dataclass
class LoopContext:
    run_id: str
    loop_id: str
    project_id: str
    agent_id: str
    task_id: str
    goal_id: str
    iteration: int = 0
    phase: str = ""
    state: LoopStateName = "CREATED"
    parent_run_id: str | None = None
    tenant_id: str = "system"
    session_id: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    evidence: list[Any] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    budgets: dict[str, Any] = field(default_factory=dict)
    errors: list[Any] = field(default_factory=list)
    recovery_state: dict[str, Any] = field(default_factory=lambda: {"repair_count": 0})
    strategy: str = "sequential"
    capability_requests: list[str] = field(default_factory=list)
    idempotency_key: str | None = None
    fingerprint: str | None = None
    created_at: str = ""
    updated_at: str = ""
    started_at: str | None = None
    closed_at: str | None = None


@dataclass(frozen=True)
class LoopCommand:
    command: LoopCommandName
    run_id: str
    issued_at: str
    issued_by: str = "system"
    reason: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = None


@dataclass(frozen=True)
class LoopEvent:
    event_id: str
    run_id: str
    type: str
    timestamp: str
    prev_hash: str
    hash: str
    phase: str | None = None
    iteration: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    actor: str = "system"


def can_transition(from_state: str, to_state: str) -> bool:
    return to_state in TRANSITIONS.get(from_state, frozenset())


def assert_transition(from_state: str, to_state: str) -> None:
    if not can_transition(from_state, to_state):
        raise ValueError(f"illegal transition {from_state} → {to_state}")
