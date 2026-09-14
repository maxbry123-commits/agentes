"""Self-improvement engine -- learns from errors and auto-improves.

Monitors tool execution patterns, detects recurring failures,
and generates improved procedures/prompts automatically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class FailurePattern:
    """A detected recurring failure pattern for a specific tool."""

    tool: str
    error_pattern: str
    count: int = 0
    first_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved: bool = False
    improvement_id: str = ""


@dataclass
class Improvement:
    """A proposed or applied improvement based on failure analysis."""

    id: str
    pattern_id: str
    improvement_type: str  # "prompt", "procedure", "tool_param"
    before: str
    after: str
    confidence: float = 0.5
    applied: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SelfImprover:
    """Tracks tool failures, detects patterns, and proposes improvements.

    When the same tool fails 3+ times with a similar error, the engine
    generates an improvement proposal that can be reviewed and applied.
    """

    FAILURE_THRESHOLD = 3  # failures before proposing improvement

    def __init__(self) -> None:
        self._patterns: dict[str, FailurePattern] = {}
        self._improvements: list[Improvement] = []

    def record_failure(
        self,
        tool: str,
        error: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Record a tool execution failure."""
        key = f"{tool}:{_normalize_error(error)}"
        if key in self._patterns:
            p = self._patterns[key]
            p.count += 1
            p.last_seen = datetime.now(UTC)
        else:
            self._patterns[key] = FailurePattern(
                tool=tool,
                error_pattern=_normalize_error(error),
            )
            self._patterns[key].count = 1

        # Check if threshold reached
        if self._patterns[key].count >= self.FAILURE_THRESHOLD and not self._patterns[key].resolved:
            self._propose_improvement(key, self._patterns[key])

    def record_success(
        self,
        tool: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Record a successful tool execution -- reduces failure pattern weight."""
        for _key, p in self._patterns.items():
            if p.tool == tool and not p.resolved:
                p.count = max(0, p.count - 1)

    def _propose_improvement(self, key: str, pattern: FailurePattern) -> None:
        """Generate an improvement proposal for a recurring failure."""
        from uuid import uuid4

        imp = Improvement(
            id=str(uuid4()),
            pattern_id=key,
            improvement_type="procedure",
            before=f"Tool '{pattern.tool}' fails with: {pattern.error_pattern}",
            after=(
                f"Suggested: Add error handling for '{pattern.error_pattern}' in {pattern.tool}"
            ),
            confidence=min(0.9, 0.3 + pattern.count * 0.1),
        )
        self._improvements.append(imp)
        pattern.improvement_id = imp.id

        log.info(
            "self_improvement_proposed",
            tool=pattern.tool,
            pattern=pattern.error_pattern,
            count=pattern.count,
            improvement_id=imp.id,
        )

    @property
    def pending_improvements(self) -> list[Improvement]:
        """Return all improvements that have not been applied yet."""
        return [i for i in self._improvements if not i.applied]

    def apply_improvement(self, improvement_id: str) -> bool:
        """Mark an improvement as applied and resolve its pattern."""
        for imp in self._improvements:
            if imp.id == improvement_id:
                imp.applied = True
                # Mark pattern as resolved
                if imp.pattern_id in self._patterns:
                    self._patterns[imp.pattern_id].resolved = True
                return True
        return False

    def stats(self) -> dict[str, Any]:
        """Return summary statistics."""
        total_patterns = len(self._patterns)
        active = sum(1 for p in self._patterns.values() if not p.resolved)
        improvements = len(self._improvements)
        applied = sum(1 for i in self._improvements if i.applied)
        return {
            "total_patterns": total_patterns,
            "active_patterns": active,
            "total_improvements": improvements,
            "applied_improvements": applied,
            "pending_improvements": improvements - applied,
        }


def _normalize_error(error: str) -> str:
    """Normalize error strings for pattern matching.

    Strips file paths, line numbers, and memory addresses so that
    structurally identical errors are grouped together.
    """
    # Remove file paths, line numbers, memory addresses
    error = re.sub(r'(?:File |at |in )"[^"]*"', "", error)
    error = re.sub(r"line \d+", "", error)
    error = re.sub(r"0x[0-9a-fA-F]+", "", error)
    return error.strip()[:200]
