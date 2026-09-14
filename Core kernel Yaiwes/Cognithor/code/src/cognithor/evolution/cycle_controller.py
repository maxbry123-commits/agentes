"""LearningCycleController — self-directed learning with autonomous exams.

Manages the Expand -> Examine -> Decide loop:
- After every 10 horizon expansions, triggers a quality exam
- Score >= 0.8 -> MASTERED (stop)
- Score < 0.8 + progress -> continue at full frequency
- Score < 0.8 + stagnating (delta < 0.05 over 2 exams) -> reduce frequency to 25%
- Stagnating + score rises -> recover to full frequency
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger(__name__)

_MASTERY_THRESHOLD = 0.8
_STAGNATION_DELTA = 0.05
_STAGNATION_COUNT = 2
_EXAM_INTERVAL = 10
_STAGNATION_FREQUENCY = 0.25


class CycleState(str, Enum):
    LEARNING = "learning"
    EXAMINING = "examining"
    MASTERED = "mastered"
    STAGNATING = "stagnating"


@dataclass
class ExamResult:
    score: float
    questions_total: int
    questions_passed: int
    gaps: list[str] = field(default_factory=list)
    expansion_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class CycleHistory:
    plan_id: str = ""
    exam_results: list[ExamResult] = field(default_factory=list)
    total_expansions: int = 0
    state: CycleState = CycleState.LEARNING
    stagnation_count: int = 0
    frequency_multiplier: float = 1.0


class CycleController:
    """Controls the self-directed learning cycle with autonomous exams."""

    def __init__(self, plans_dir: Path | None = None) -> None:
        self._histories: dict[str, CycleHistory] = {}
        self._plans_dir = plans_dir

    @property
    def state(self) -> CycleState:
        if not self._histories:
            return CycleState.LEARNING
        last = list(self._histories.values())[-1]
        return last.state

    @property
    def frequency_multiplier(self) -> float:
        if not self._histories:
            return 1.0
        last = list(self._histories.values())[-1]
        return last.frequency_multiplier

    def after_expansion(self, plan_id: str, expansion_count: int) -> ExamResult | None:
        history = self._get_or_create(plan_id)
        history.total_expansions = expansion_count
        if expansion_count % _EXAM_INTERVAL != 0:
            return None
        history.state = CycleState.EXAMINING
        return None

    def record_exam(self, plan_id: str, exam: ExamResult) -> CycleState:
        history = self._get_or_create(plan_id)
        history.exam_results.append(exam)
        history.total_expansions = max(
            history.total_expansions,
            len(history.exam_results) * _EXAM_INTERVAL,
        )

        if exam.score >= _MASTERY_THRESHOLD:
            history.state = CycleState.MASTERED
            history.frequency_multiplier = 0.0
            log.info("cycle_mastered", plan_id=plan_id, score=exam.score)
            self._persist(plan_id)
            return history.state

        if len(history.exam_results) >= 2:
            delta = exam.score - history.exam_results[-2].score
            if delta < _STAGNATION_DELTA:
                history.stagnation_count += 1
            else:
                history.stagnation_count = 0
                if history.state == CycleState.STAGNATING:
                    history.state = CycleState.LEARNING
                    history.frequency_multiplier = 1.0
                    log.info("cycle_recovered", plan_id=plan_id, delta=round(delta, 3))

        if history.stagnation_count >= _STAGNATION_COUNT and history.state != CycleState.STAGNATING:
            history.state = CycleState.STAGNATING
            history.frequency_multiplier = _STAGNATION_FREQUENCY
            log.info("cycle_stagnating", plan_id=plan_id, score=exam.score)
        elif history.state not in (CycleState.STAGNATING, CycleState.MASTERED):
            history.state = CycleState.LEARNING

        self._persist(plan_id)
        return history.state

    def get_history(self, plan_id: str) -> CycleHistory:
        return self._get_or_create(plan_id)

    def get_gaps(self, plan_id: str) -> list[str]:
        history = self._histories.get(plan_id)
        if not history or not history.exam_results:
            return []
        return history.exam_results[-1].gaps

    def should_skip_cycle(self, plan_id: str) -> bool:
        history = self._histories.get(plan_id)
        if not history:
            return False
        if history.state == CycleState.MASTERED:
            return True
        if history.state == CycleState.STAGNATING:
            return random.random() > history.frequency_multiplier
        return False

    def stats(self) -> dict[str, Any]:
        return {
            "plans": len(self._histories),
            "mastered": sum(1 for h in self._histories.values() if h.state == CycleState.MASTERED),
            "stagnating": sum(
                1 for h in self._histories.values() if h.state == CycleState.STAGNATING
            ),
            "learning": sum(1 for h in self._histories.values() if h.state == CycleState.LEARNING),
        }

    def _get_or_create(self, plan_id: str) -> CycleHistory:
        if plan_id not in self._histories:
            self._histories[plan_id] = CycleHistory(plan_id=plan_id)
            self._load(plan_id)
        return self._histories[plan_id]

    def _persist(self, plan_id: str) -> None:
        if not self._plans_dir:
            return
        plan_dir = self._plans_dir / plan_id
        plan_dir.mkdir(parents=True, exist_ok=True)
        path = plan_dir / "cycle_history.json"
        history = self._histories[plan_id]
        data = {
            "plan_id": history.plan_id,
            "state": history.state.value,
            "total_expansions": history.total_expansions,
            "stagnation_count": history.stagnation_count,
            "frequency_multiplier": history.frequency_multiplier,
            "exam_results": [
                {
                    "score": e.score,
                    "questions_total": e.questions_total,
                    "questions_passed": e.questions_passed,
                    "gaps": e.gaps,
                    "expansion_count": e.expansion_count,
                    "timestamp": e.timestamp,
                }
                for e in history.exam_results
            ],
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self, plan_id: str) -> None:
        if not self._plans_dir:
            return
        path = self._plans_dir / plan_id / "cycle_history.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            history = self._histories[plan_id]
            history.state = CycleState(data.get("state", "learning"))
            history.total_expansions = data.get("total_expansions", 0)
            history.stagnation_count = data.get("stagnation_count", 0)
            history.frequency_multiplier = data.get("frequency_multiplier", 1.0)
            history.exam_results = [ExamResult(**e) for e in data.get("exam_results", [])]
        except Exception:
            log.debug("cycle_history_load_failed", plan_id=plan_id, exc_info=True)
