"""W03 · Failure Contract · recovery sin boolean crudo."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional
import time


class FailureType(str, Enum):
    VALIDATION = "validation"
    CONTRACT = "contract"
    AGENT = "agent"
    TIMEOUT = "timeout"
    API_BUDGET = "api_budget"
    SANDBOX = "sandbox"
    GITHUB = "github"
    MEMORY = "memory"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    RETRY = "retry"
    FALLBACK_AGENT = "fallback_agent"
    REPLAN = "replan"
    CHECKPOINT_RESUME = "checkpoint_resume"
    ESCALATE = "escalate"
    ABORT = "abort"
    WAIT = "wait"


@dataclass
class Failure:
    type: FailureType
    detail: str
    retryable: bool
    evidence: dict[str, Any] = field(default_factory=dict)
    affected_node: str = ""
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    timestamp: float = field(default_factory=time.time)
    mission_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["type"] = self.type.value
        d["recovery_strategy"] = self.recovery_strategy.value
        return d

    @staticmethod
    def from_exception(
        exc: BaseException,
        *,
        type: FailureType = FailureType.UNKNOWN,
        retryable: bool = True,
        recovery: RecoveryStrategy = RecoveryStrategy.RETRY,
        evidence: dict | None = None,
        affected_node: str = "",
        mission_id: str = "",
    ) -> "Failure":
        return Failure(
            type=type,
            detail=str(exc),
            retryable=retryable,
            evidence=dict(evidence or {}),
            affected_node=affected_node,
            recovery_strategy=recovery,
            mission_id=mission_id,
        )


def choose_recovery(f: Failure, *, retries_done: int = 0, max_retries: int = 3) -> RecoveryStrategy:
    """Política determinista simple."""
    if not f.retryable:
        return RecoveryStrategy.ESCALATE if f.type != FailureType.VALIDATION else RecoveryStrategy.ABORT
    if f.type == FailureType.API_BUDGET:
        return RecoveryStrategy.WAIT
    if f.type == FailureType.SANDBOX:
        return RecoveryStrategy.CHECKPOINT_RESUME
    if retries_done >= max_retries:
        return RecoveryStrategy.FALLBACK_AGENT if f.type == FailureType.AGENT else RecoveryStrategy.ESCALATE
    return f.recovery_strategy or RecoveryStrategy.RETRY
