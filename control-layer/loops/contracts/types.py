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

DetectorName = Literal[
    "stall", "oscillation", "regression", "drift", "budget", "timeout",
    "invalid_output", "contract_violation", "dependency_failure",
    "resource_exhaustion", "repeated_failure", "goal_drift", "no_progress",
]

PolicyAction = Literal[
    "CONTINUE", "REPAIR", "RETRY", "REFRAME", "CHANGE_STRATEGY",
    "CHANGE_MODEL", "CHANGE_AGENT", "REDUCE_SCOPE", "ROLLBACK",
    "ISOLATE", "CHECKPOINT", "ESCALATE", "ABORT", "CLOSE", "HUMAN_GATE",
]

BudgetLevel = Literal["micro", "tarea", "fase", "proyecto"]

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

LEVEL_DEFAULTS: dict[str, dict[str, int | float]] = {
    "micro": {"tokens": 20000, "time_seg": 600, "max_iter": 5, "model_calls": 10, "tool_calls": 20},
    "tarea": {"tokens": 80000, "time_seg": 2700, "max_iter": 8, "model_calls": 40, "tool_calls": 80},
    "fase": {"tokens": 300000, "time_seg": 10800, "max_iter": 12, "model_calls": 120, "tool_calls": 200},
    "proyecto": {"tokens": 1500000, "time_seg": 86400, "max_iter": 20, "model_calls": 500, "tool_calls": 1000},
}


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


@dataclass(frozen=True)
class DetectorResult:
    detector: DetectorName
    severity: float
    fired_at: str
    run_id: str = ""
    evidence: list[Any] = field(default_factory=list)
    action_hint: str | None = None
    iteration: int | None = None
    phase: str | None = None


@dataclass(frozen=True)
class PolicyDecision:
    action: PolicyAction
    run_id: str
    reason: str
    decided_at: str
    triggered_by: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    policy_rule_id: str | None = None


@dataclass
class Budget:
    level: BudgetLevel = "tarea"
    token_budget: int = 80000
    time_budget_seg: int = 2700
    iteration_budget: int = 8
    tool_call_budget: int = 80
    model_call_budget: int = 40
    parallelism_budget: int = 1
    cost_budget: float = 0.0
    memory_budget_mb: int = 0
    retry_budget: int = 2
    tokens_used: int = 0
    time_used_seg: float = 0.0
    iterations_used: int = 0
    tool_calls_used: int = 0
    model_calls_used: int = 0
    cost_used: float = 0.0
    retries_used: int = 0

    def exhausted(self) -> list[str]:
        out: list[str] = []
        if self.tokens_used >= self.token_budget > 0:
            out.append("tokens")
        if self.time_used_seg >= self.time_budget_seg > 0:
            out.append("time")
        if self.iterations_used >= self.iteration_budget:
            out.append("iterations")
        if self.tool_calls_used >= self.tool_call_budget > 0:
            out.append("tool_calls")
        if self.model_calls_used >= self.model_call_budget > 0:
            out.append("model_calls")
        if self.retries_used >= self.retry_budget:
            out.append("retries")
        return out

    def warning_80(self) -> list[str]:
        out: list[str] = []
        for name, used, lim in [
            ("tokens", self.tokens_used, self.token_budget),
            ("time", self.time_used_seg, self.time_budget_seg),
            ("iterations", self.iterations_used, self.iteration_budget),
        ]:
            if lim > 0 and used >= 0.8 * lim:
                out.append(name)
        return out


@dataclass(frozen=True)
class ProgressResult:
    progress_score: float
    confidence: float
    evaluated_at: str
    kind: str = "numeric"
    details: dict[str, Any] = field(default_factory=dict)
    threshold: float = 0.1
    delta_vs_prev: float | None = None
    evaluator_id: str | None = None

    def is_stalled(self) -> bool:
        return self.progress_score < self.threshold


def can_transition(from_state: str, to_state: str) -> bool:
    return to_state in TRANSITIONS.get(from_state, frozenset())


def assert_transition(from_state: str, to_state: str) -> None:
    if not can_transition(from_state, to_state):
        raise ValueError(f"illegal transition {from_state} → {to_state}")
