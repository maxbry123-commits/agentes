"""ProgressEvaluator + Adaptive Iteration · 0% LLM (numeric path)
SOURCE: progress_result.schema · Adaptive Iteration Controller
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from loops.contracts.types import ProgressResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProgressEvaluator:
    """Normaliza progreso a [0,1]. kinds: numeric|boolean|tests|validation|evidence."""

    def evaluate(
        self,
        *,
        kind: str = "numeric",
        value: Any = None,
        prev_score: float | None = None,
        threshold: float = 0.1,
        details: dict[str, Any] | None = None,
        evaluator_id: str = "progress.v1",
    ) -> ProgressResult:
        score = 0.0
        confidence = 0.7
        d = dict(details or {})

        if kind == "numeric":
            try:
                score = max(0.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                score = 0.0
                confidence = 0.3
        elif kind == "boolean":
            score = 1.0 if value else 0.0
            confidence = 0.9
        elif kind == "tests":
            # value = {passed, total}
            if isinstance(value, dict) and value.get("total"):
                score = float(value.get("passed", 0)) / float(value["total"])
                confidence = 0.85
            else:
                score = 0.0
                confidence = 0.4
        elif kind == "validation":
            score = 1.0 if value else 0.0
            confidence = 0.9
        elif kind == "evidence":
            # value = count of evidence items, soft cap at 5
            n = int(value or 0)
            score = min(1.0, n / 5.0)
            confidence = 0.6
        else:
            # custom / unknown → 0 with low confidence
            score = 0.0
            confidence = 0.2
            d["warning"] = f"unsupported kind={kind}"

        delta = None if prev_score is None else score - prev_score
        return ProgressResult(
            progress_score=score,
            confidence=confidence,
            evaluated_at=_now(),
            kind=kind,
            details=d,
            threshold=threshold,
            delta_vs_prev=delta,
            evaluator_id=evaluator_id,
        )


@dataclass
class AdaptiveAdvice:
    continue_loop: bool
    reason: str
    suggest_action: str  # CONTINUE|REPAIR|CHANGE_STRATEGY|CLOSE|ESCALATE


class AdaptiveIterationController:
    """Decide si seguir iterando según progreso (sin max_iter ciego)."""

    def __init__(self, max_iter: int = 8, stall_limit: int = 2):
        self.max_iter = max_iter
        self.stall_limit = stall_limit
        self._stall_streak = 0

    def advise(self, progress: ProgressResult, iteration: int) -> AdaptiveAdvice:
        if iteration >= self.max_iter:
            return AdaptiveAdvice(False, "max_iter", "ESCALATE" if progress.progress_score < 0.5 else "CLOSE")

        if progress.progress_score >= 0.95 and progress.confidence >= 0.7:
            return AdaptiveAdvice(False, "excellent_progress", "CLOSE")

        if progress.is_stalled():
            self._stall_streak += 1
        else:
            self._stall_streak = 0

        if self._stall_streak >= self.stall_limit:
            if self._stall_streak >= self.stall_limit + 2:
                return AdaptiveAdvice(False, "stall_persistent", "ESCALATE")
            return AdaptiveAdvice(True, "stall", "CHANGE_STRATEGY")

        if progress.delta_vs_prev is not None and progress.delta_vs_prev < -0.15 and progress.confidence > 0.5:
            return AdaptiveAdvice(True, "regression", "REPAIR")

        if progress.progress_score >= progress.threshold:
            return AdaptiveAdvice(True, "progress_ok", "CONTINUE")

        return AdaptiveAdvice(True, "low_progress", "REPAIR")
