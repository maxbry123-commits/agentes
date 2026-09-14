"""Failure-Taxonomy and Recovery Recipes.

Classifies runtime failures into structured categories and provides
automatic recovery recipes. Inspired by Claw Code's recovery_recipes pattern.

Each FailureClass maps to a RecoveryRecipe with ordered steps.
The RecoveryEngine classifies exceptions and attempts one recovery
before escalating to the user.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# ============================================================================
# Failure Classification
# ============================================================================


class FailureClass(str, Enum):
    """Structured failure categories covering all Cognithor failure modes."""

    LLM_TIMEOUT = "llm_timeout"
    LLM_CONNECTION = "llm_connection"
    LLM_RATE_LIMIT = "llm_rate_limit"
    TOOL_RUNTIME = "tool_runtime"
    TOOL_TIMEOUT = "tool_timeout"
    GATEKEEPER_BLOCK = "gatekeeper_block"
    MCP_ERROR = "mcp_error"
    INFRA = "infra"


class RecoveryStep(str, Enum):
    """Atomic recovery actions."""

    RETRY = "retry"
    SWITCH_PROVIDER = "switch_provider"
    CLEAR_CACHE = "clear_cache"
    RESTART_MODULE = "restart_module"
    ESCALATE_TO_USER = "escalate_to_user"


class EscalationPolicy(str, Enum):
    """What to do when recovery fails."""

    ALERT_USER = "alert_user"
    LOG_AND_CONTINUE = "log_and_continue"
    ABORT = "abort"


# ============================================================================
# Recovery Recipe
# ============================================================================


@dataclass(frozen=True)
class RecoveryRecipe:
    """Defines how to recover from a specific failure class."""

    failure_class: FailureClass
    steps: tuple[RecoveryStep, ...]
    max_attempts: int = 1
    escalation: EscalationPolicy = EscalationPolicy.ALERT_USER


# Default recipes for each failure class
DEFAULT_RECIPES: dict[FailureClass, RecoveryRecipe] = {
    FailureClass.LLM_TIMEOUT: RecoveryRecipe(
        failure_class=FailureClass.LLM_TIMEOUT,
        steps=(RecoveryStep.RETRY, RecoveryStep.SWITCH_PROVIDER),
        max_attempts=2,
        escalation=EscalationPolicy.ALERT_USER,
    ),
    FailureClass.LLM_CONNECTION: RecoveryRecipe(
        failure_class=FailureClass.LLM_CONNECTION,
        steps=(RecoveryStep.RETRY, RecoveryStep.SWITCH_PROVIDER),
        max_attempts=2,
        escalation=EscalationPolicy.ALERT_USER,
    ),
    FailureClass.LLM_RATE_LIMIT: RecoveryRecipe(
        failure_class=FailureClass.LLM_RATE_LIMIT,
        steps=(RecoveryStep.SWITCH_PROVIDER, RecoveryStep.RETRY),
        max_attempts=1,
        escalation=EscalationPolicy.ALERT_USER,
    ),
    FailureClass.TOOL_RUNTIME: RecoveryRecipe(
        failure_class=FailureClass.TOOL_RUNTIME,
        steps=(RecoveryStep.RETRY, RecoveryStep.CLEAR_CACHE),
        max_attempts=2,
        escalation=EscalationPolicy.ALERT_USER,
    ),
    FailureClass.TOOL_TIMEOUT: RecoveryRecipe(
        failure_class=FailureClass.TOOL_TIMEOUT,
        steps=(RecoveryStep.RETRY,),
        max_attempts=2,
        escalation=EscalationPolicy.ALERT_USER,
    ),
    FailureClass.GATEKEEPER_BLOCK: RecoveryRecipe(
        failure_class=FailureClass.GATEKEEPER_BLOCK,
        steps=(RecoveryStep.ESCALATE_TO_USER,),
        max_attempts=1,
        escalation=EscalationPolicy.ALERT_USER,
    ),
    FailureClass.MCP_ERROR: RecoveryRecipe(
        failure_class=FailureClass.MCP_ERROR,
        steps=(RecoveryStep.RESTART_MODULE, RecoveryStep.RETRY),
        max_attempts=2,
        escalation=EscalationPolicy.LOG_AND_CONTINUE,
    ),
    FailureClass.INFRA: RecoveryRecipe(
        failure_class=FailureClass.INFRA,
        steps=(RecoveryStep.ESCALATE_TO_USER,),
        max_attempts=1,
        escalation=EscalationPolicy.ABORT,
    ),
}


# ============================================================================
# Recovery Event & Result
# ============================================================================


@dataclass
class RecoveryEvent:
    """A single recovery step attempt."""

    failure_class: FailureClass
    step: RecoveryStep
    attempt: int
    success: bool
    detail: str = ""
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class RecoveryResult:
    """Outcome of a recovery attempt."""

    recovered: bool
    failure_class: FailureClass
    events: list[RecoveryEvent] = field(default_factory=list)
    escalation: EscalationPolicy | None = None
    original_error: str = ""

    @property
    def steps_taken(self) -> int:
        return len(self.events)


# ============================================================================
# Exception Classification
# ============================================================================

# Map exception type names to failure classes
_EXCEPTION_MAP: dict[str, FailureClass] = {
    "TimeoutError": FailureClass.TOOL_TIMEOUT,
    "asyncio.TimeoutError": FailureClass.TOOL_TIMEOUT,
    "ConnectionError": FailureClass.LLM_CONNECTION,
    "ConnectError": FailureClass.LLM_CONNECTION,
    "ConnectionRefusedError": FailureClass.LLM_CONNECTION,
    "OllamaError": FailureClass.LLM_CONNECTION,
    "ReadTimeout": FailureClass.LLM_TIMEOUT,
    "HTTPStatusError": FailureClass.LLM_CONNECTION,
    "PermissionError": FailureClass.GATEKEEPER_BLOCK,
    "FileNotFoundError": FailureClass.INFRA,
    "MemoryError": FailureClass.INFRA,
    "OSError": FailureClass.INFRA,
    "IOError": FailureClass.INFRA,
}

# Keywords in error messages that override classification
_ERROR_KEYWORDS: dict[str, FailureClass] = {
    "rate limit": FailureClass.LLM_RATE_LIMIT,
    "429": FailureClass.LLM_RATE_LIMIT,
    "quota": FailureClass.LLM_RATE_LIMIT,
    "timeout": FailureClass.LLM_TIMEOUT,
    "timed out": FailureClass.LLM_TIMEOUT,
    "gatekeeper": FailureClass.GATEKEEPER_BLOCK,
    "blocked": FailureClass.GATEKEEPER_BLOCK,
    "mcp": FailureClass.MCP_ERROR,
    "handshake": FailureClass.MCP_ERROR,
    "disk": FailureClass.INFRA,
    "no space": FailureClass.INFRA,
}


def classify_failure(exc: BaseException, context: str = "") -> FailureClass:
    """Classify an exception into a FailureClass.

    Uses exception type first, then falls back to keyword matching
    in the error message.
    """
    exc_type = type(exc).__name__

    # Direct type match
    if exc_type in _EXCEPTION_MAP:
        return _EXCEPTION_MAP[exc_type]

    # Check MRO for parent class matches
    for cls in type(exc).__mro__:
        if cls.__name__ in _EXCEPTION_MAP:
            return _EXCEPTION_MAP[cls.__name__]

    # Keyword matching in error message
    error_text = f"{exc} {context}".lower()
    for keyword, failure_class in _ERROR_KEYWORDS.items():
        if keyword in error_text:
            return failure_class

    # Default: tool runtime error
    return FailureClass.TOOL_RUNTIME


# ============================================================================
# Recovery Engine
# ============================================================================


class RecoveryEngine:
    """Attempts structured recovery from classified failures.

    Usage:
        engine = RecoveryEngine()
        failure_class = engine.classify(exception)
        result = engine.get_recipe(failure_class)
        # Caller decides which steps to execute
    """

    def __init__(
        self,
        recipes: dict[FailureClass, RecoveryRecipe] | None = None,
    ) -> None:
        self._recipes = recipes or dict(DEFAULT_RECIPES)
        self._attempt_counts: dict[str, int] = {}

    def classify(self, exc: BaseException, context: str = "") -> FailureClass:
        """Classify an exception into a FailureClass."""
        return classify_failure(exc, context)

    def get_recipe(self, failure_class: FailureClass) -> RecoveryRecipe:
        """Get the recovery recipe for a failure class."""
        return self._recipes.get(failure_class, DEFAULT_RECIPES[FailureClass.TOOL_RUNTIME])

    def should_retry(
        self,
        failure_class: FailureClass,
        tool_name: str,
        attempt: int,
    ) -> bool:
        """Check if a retry should be attempted based on recipe and attempt count."""
        recipe = self.get_recipe(failure_class)

        # Check if RETRY is in the recipe steps
        if RecoveryStep.RETRY not in recipe.steps:
            return False

        # Check attempt limit
        key = f"{tool_name}:{failure_class.value}"
        current = self._attempt_counts.get(key, 0)
        if current >= recipe.max_attempts:
            return False

        self._attempt_counts[key] = current + 1
        return True

    def record_recovery(
        self,
        failure_class: FailureClass,
        step: RecoveryStep,
        attempt: int,
        success: bool,
        detail: str = "",
    ) -> RecoveryEvent:
        """Record a recovery attempt event."""
        event = RecoveryEvent(
            failure_class=failure_class,
            step=step,
            attempt=attempt,
            success=success,
            detail=detail,
        )
        log.info(
            "recovery_event",
            failure_class=failure_class.value,
            step=step.value,
            attempt=attempt,
            success=success,
            detail=detail[:200],
        )
        return event

    def build_result(
        self,
        failure_class: FailureClass,
        recovered: bool,
        events: list[RecoveryEvent],
        original_error: str = "",
    ) -> RecoveryResult:
        """Build a structured RecoveryResult."""
        recipe = self.get_recipe(failure_class)
        return RecoveryResult(
            recovered=recovered,
            failure_class=failure_class,
            events=events,
            escalation=None if recovered else recipe.escalation,
            original_error=original_error,
        )

    def reset(self, tool_name: str | None = None) -> None:
        """Reset attempt counters. If tool_name given, reset only that tool."""
        if tool_name:
            keys_to_remove = [k for k in self._attempt_counts if k.startswith(f"{tool_name}:")]
            for k in keys_to_remove:
                del self._attempt_counts[k]
        else:
            self._attempt_counts.clear()

    def stats(self) -> dict[str, Any]:
        """Return recovery statistics."""
        return {
            "recipes": len(self._recipes),
            "active_counters": len(self._attempt_counts),
            "counters": dict(self._attempt_counts),
        }
