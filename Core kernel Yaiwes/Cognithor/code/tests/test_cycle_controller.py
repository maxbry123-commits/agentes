"""Tests for LearningCycleController."""

from __future__ import annotations

from cognithor.evolution.cycle_controller import (
    CycleController,
    CycleState,
    ExamResult,
)


def _make_exam(
    score: float, gaps: list[str] | None = None, expansion_count: int = 10
) -> ExamResult:
    return ExamResult(
        score=score,
        questions_total=10,
        questions_passed=int(score * 10),
        gaps=gaps or [],
        expansion_count=expansion_count,
    )


class TestCycleState:
    def test_all_states(self):
        assert len(CycleState) == 4


class TestCycleController:
    def test_initial_state(self):
        ctrl = CycleController()
        assert ctrl.state == CycleState.LEARNING
        assert ctrl.frequency_multiplier == 1.0

    def test_no_exam_before_10(self):
        ctrl = CycleController()
        result = ctrl.after_expansion("plan1", 5)
        assert result is None

    def test_exam_at_10(self):
        ctrl = CycleController()
        exam = _make_exam(0.6, gaps=["topic A"])
        ctrl.record_exam("plan1", exam)
        assert ctrl.state == CycleState.LEARNING

    def test_mastered_at_08(self):
        ctrl = CycleController()
        exam = _make_exam(0.85)
        ctrl.record_exam("plan1", exam)
        assert ctrl.state == CycleState.MASTERED

    def test_stagnation_after_2_low_deltas(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.5))
        ctrl.record_exam("plan1", _make_exam(0.52))
        ctrl.record_exam("plan1", _make_exam(0.53))
        assert ctrl.state == CycleState.STAGNATING
        assert ctrl.frequency_multiplier == 0.25

    def test_recovery_from_stagnation(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.5))
        ctrl.record_exam("plan1", _make_exam(0.52))
        ctrl.record_exam("plan1", _make_exam(0.53))
        assert ctrl.state == CycleState.STAGNATING
        ctrl.record_exam("plan1", _make_exam(0.65))
        assert ctrl.state == CycleState.LEARNING
        assert ctrl.frequency_multiplier == 1.0

    def test_history_persists(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.4))
        ctrl.record_exam("plan1", _make_exam(0.5))
        history = ctrl.get_history("plan1")
        assert len(history.exam_results) == 2
        assert history.total_expansions == 20

    def test_gaps_returned(self):
        ctrl = CycleController()
        exam = _make_exam(0.6, gaps=["VVG Basics", "Haftpflicht"])
        ctrl.record_exam("plan1", exam)
        gaps = ctrl.get_gaps("plan1")
        assert "VVG Basics" in gaps
        assert "Haftpflicht" in gaps

    def test_should_skip_cycle_stagnating(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.5))
        ctrl.record_exam("plan1", _make_exam(0.52))
        ctrl.record_exam("plan1", _make_exam(0.53))
        skips = sum(1 for i in range(100) if ctrl.should_skip_cycle("plan1"))
        assert skips >= 50  # ~75% skip rate at 0.25 frequency, allow statistical variance

    def test_mastered_always_skips(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.9))
        assert ctrl.should_skip_cycle("plan1") is True
