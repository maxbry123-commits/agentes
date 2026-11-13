"""End-to-end integration test for Evolution Engine learning cycle."""

from __future__ import annotations

from cognithor.evolution.cycle_controller import CycleController, CycleState, ExamResult


class TestEvolutionE2E:
    """Simulate a complete learning cycle: expand -> exam -> stagnate -> recover -> master."""

    def test_full_learning_lifecycle(self, tmp_path):
        """Simulate 60 expansions with exams every 10."""
        ctrl = CycleController(plans_dir=tmp_path)

        # Phase 1: Learning (expansions 1-10, first exam at 10)
        for i in range(1, 11):
            ctrl.after_expansion("insurance", i)
        ctrl.record_exam(
            "insurance",
            ExamResult(
                score=0.35,
                questions_total=10,
                questions_passed=3,
                gaps=["VVG Grundlagen", "Haftpflicht"],
                expansion_count=10,
            ),
        )
        assert ctrl.get_history("insurance").state == CycleState.LEARNING
        assert ctrl.get_gaps("insurance") == ["VVG Grundlagen", "Haftpflicht"]

        # Phase 2: Progress (exam at 20 — score improved)
        ctrl.record_exam(
            "insurance",
            ExamResult(
                score=0.50,
                questions_total=10,
                questions_passed=5,
                gaps=["Haftpflicht"],
                expansion_count=20,
            ),
        )
        assert ctrl.get_history("insurance").state == CycleState.LEARNING

        # Phase 3: Stagnation starts (exam at 30 — tiny improvement)
        ctrl.record_exam(
            "insurance",
            ExamResult(
                score=0.52,
                questions_total=10,
                questions_passed=5,
                gaps=["Haftpflicht"],
                expansion_count=30,
            ),
        )
        # delta = 0.02 < 0.05 → stagnation_count = 1, not yet STAGNATING

        # Phase 4: Stagnation confirmed (exam at 40 — still tiny)
        ctrl.record_exam(
            "insurance",
            ExamResult(
                score=0.53,
                questions_total=10,
                questions_passed=5,
                gaps=["Haftpflicht"],
                expansion_count=40,
            ),
        )
        assert ctrl.get_history("insurance").state == CycleState.STAGNATING
        assert ctrl.get_history("insurance").frequency_multiplier == 0.25

        # Phase 5: Recovery (exam at 50 — big jump, new sources found)
        ctrl.record_exam(
            "insurance",
            ExamResult(
                score=0.70,
                questions_total=10,
                questions_passed=7,
                gaps=[],
                expansion_count=50,
            ),
        )
        assert ctrl.get_history("insurance").state == CycleState.LEARNING
        assert ctrl.get_history("insurance").frequency_multiplier == 1.0

        # Phase 6: Mastery (exam at 60 — passed!)
        ctrl.record_exam(
            "insurance",
            ExamResult(
                score=0.85,
                questions_total=10,
                questions_passed=8,
                gaps=[],
                expansion_count=60,
            ),
        )
        assert ctrl.get_history("insurance").state == CycleState.MASTERED
        assert ctrl.should_skip_cycle("insurance") is True

        # Verify history
        history = ctrl.get_history("insurance")
        assert len(history.exam_results) == 6
        assert history.total_expansions == 60

    def test_persistence_across_restarts(self, tmp_path):
        """Verify cycle history survives controller restart."""
        # First run
        ctrl1 = CycleController(plans_dir=tmp_path)
        ctrl1.record_exam(
            "goal1",
            ExamResult(
                score=0.45,
                questions_total=10,
                questions_passed=4,
                expansion_count=10,
            ),
        )
        assert ctrl1.get_history("goal1").state == CycleState.LEARNING

        # Simulate restart
        ctrl2 = CycleController(plans_dir=tmp_path)
        history = ctrl2.get_history("goal1")
        assert len(history.exam_results) == 1
        assert history.exam_results[0].score == 0.45
        assert history.state == CycleState.LEARNING

    def test_multiple_goals_independent(self, tmp_path):
        """Different goals have independent cycle states."""
        ctrl = CycleController(plans_dir=tmp_path)

        # Goal A: mastered quickly
        ctrl.record_exam(
            "goalA",
            ExamResult(score=0.9, questions_total=10, questions_passed=9, expansion_count=10),
        )
        assert ctrl.get_history("goalA").state == CycleState.MASTERED

        # Goal B: still learning
        ctrl.record_exam(
            "goalB",
            ExamResult(score=0.4, questions_total=10, questions_passed=4, expansion_count=10),
        )
        assert ctrl.get_history("goalB").state == CycleState.LEARNING

        # They don't interfere
        assert ctrl.should_skip_cycle("goalA") is True
        assert ctrl.should_skip_cycle("goalB") is False

    def test_stats(self, tmp_path):
        ctrl = CycleController(plans_dir=tmp_path)
        ctrl.record_exam(
            "a", ExamResult(score=0.9, questions_total=5, questions_passed=5, expansion_count=10)
        )
        ctrl.record_exam(
            "b", ExamResult(score=0.4, questions_total=5, questions_passed=2, expansion_count=10)
        )

        stats = ctrl.stats()
        assert stats["plans"] == 2
        assert stats["mastered"] == 1
        assert stats["learning"] == 1
