"""Tests for the Memory Importance Scorer.

Covers decay strategies, composite scoring, frequency tracking,
weight validation, batch scoring, and threshold filtering.
"""

from __future__ import annotations

import math

import pytest

from cognithor.memory.scoring import (
    DecayStrategy,
    FrequencyTracker,
    ImportanceScorer,
    MemoryScore,
    ScoringWeights,
)

# ============================================================================
# ScoringWeights
# ============================================================================


class TestScoringWeights:
    def test_default_weights_sum_to_1(self) -> None:
        w = ScoringWeights()
        total = w.relevance + w.recency + w.frequency + w.source_trust
        assert abs(total - 1.0) < 0.01

    def test_custom_weights(self) -> None:
        w = ScoringWeights(relevance=0.25, recency=0.25, frequency=0.25, source_trust=0.25)
        assert w.relevance == 0.25

    def test_invalid_weights_raise(self) -> None:
        with pytest.raises(ValueError, match="must sum to 1.0"):
            ScoringWeights(relevance=0.5, recency=0.5, frequency=0.5, source_trust=0.5)


# ============================================================================
# MemoryScore
# ============================================================================


class TestMemoryScore:
    def test_above_threshold_high(self) -> None:
        s = MemoryScore(entry_id="a", composite=0.5)
        assert s.above_threshold is True

    def test_above_threshold_low(self) -> None:
        s = MemoryScore(entry_id="a", composite=0.1)
        assert s.above_threshold is False

    def test_above_threshold_boundary(self) -> None:
        s = MemoryScore(entry_id="a", composite=0.2)
        assert s.above_threshold is True


# ============================================================================
# FrequencyTracker
# ============================================================================


class TestFrequencyTracker:
    def test_initial_state(self) -> None:
        ft = FrequencyTracker()
        assert ft.total_entries == 0
        assert ft.total_accesses == 0
        assert ft.get_normalized("x") == 0.0

    def test_single_access(self) -> None:
        ft = FrequencyTracker()
        ft.record_access("a")
        assert ft.get_count("a") == 1
        assert ft.get_normalized("a") == 1.0

    def test_multiple_accesses(self) -> None:
        ft = FrequencyTracker()
        ft.record_access("a")
        ft.record_access("a")
        ft.record_access("b")
        assert ft.get_count("a") == 2
        assert ft.get_count("b") == 1
        assert ft.get_normalized("a") == 1.0
        assert ft.get_normalized("b") == 0.5

    def test_unknown_entry(self) -> None:
        ft = FrequencyTracker()
        ft.record_access("a")
        assert ft.get_count("x") == 0
        assert ft.get_normalized("x") == 0.0

    def test_totals(self) -> None:
        ft = FrequencyTracker()
        ft.record_access("a")
        ft.record_access("a")
        ft.record_access("b")
        assert ft.total_entries == 2
        assert ft.total_accesses == 3


# ============================================================================
# Decay Strategies
# ============================================================================


class TestDecayStrategies:
    def setup_method(self) -> None:
        self.scorer = ImportanceScorer(half_life_days=30.0)

    def test_exponential_at_zero(self) -> None:
        assert self.scorer.compute_recency(0.0) == pytest.approx(1.0)

    def test_exponential_at_half_life(self) -> None:
        score = self.scorer.compute_recency(30.0)
        assert score == pytest.approx(math.exp(-1), rel=1e-6)

    def test_exponential_at_double_half_life(self) -> None:
        score = self.scorer.compute_recency(60.0)
        assert score == pytest.approx(math.exp(-2), rel=1e-6)

    def test_exponential_negative_age(self) -> None:
        # Negative age should be treated as 0
        assert self.scorer.compute_recency(-5.0) == pytest.approx(1.0)

    def test_linear_decay(self) -> None:
        scorer = ImportanceScorer(decay_strategy=DecayStrategy.LINEAR, max_age_days=100.0)
        assert scorer.compute_recency(0.0) == pytest.approx(1.0)
        assert scorer.compute_recency(50.0) == pytest.approx(0.5)
        assert scorer.compute_recency(100.0) == pytest.approx(0.0)
        assert scorer.compute_recency(200.0) == pytest.approx(0.0)

    def test_step_decay_fresh(self) -> None:
        scorer = ImportanceScorer(
            decay_strategy=DecayStrategy.STEP,
            step_threshold_days=90.0,
            step_low_value=0.2,
        )
        assert scorer.compute_recency(10.0) == 1.0

    def test_step_decay_old(self) -> None:
        scorer = ImportanceScorer(
            decay_strategy=DecayStrategy.STEP,
            step_threshold_days=90.0,
            step_low_value=0.2,
        )
        assert scorer.compute_recency(100.0) == 0.2

    def test_none_decay(self) -> None:
        scorer = ImportanceScorer(decay_strategy=DecayStrategy.NONE)
        assert scorer.compute_recency(0.0) == 1.0
        assert scorer.compute_recency(1000.0) == 1.0


# ============================================================================
# ImportanceScorer
# ============================================================================


class TestImportanceScorer:
    def test_score_fresh_relevant_entry(self) -> None:
        scorer = ImportanceScorer()
        score = scorer.score_entry("e1", relevance=0.9, age_days=0, source_confidence=0.8)
        assert score.composite > 0.5
        assert score.relevance == 0.9
        assert score.recency == pytest.approx(1.0)

    def test_score_old_irrelevant_entry(self) -> None:
        scorer = ImportanceScorer()
        score = scorer.score_entry("e2", relevance=0.1, age_days=365, source_confidence=0.3)
        assert score.composite < 0.3

    def test_score_clamps_relevance(self) -> None:
        scorer = ImportanceScorer()
        score = scorer.score_entry("e3", relevance=1.5, age_days=0, source_confidence=0.5)
        assert score.relevance == 1.0  # Clamped

    def test_score_clamps_negative_relevance(self) -> None:
        scorer = ImportanceScorer()
        score = scorer.score_entry("e4", relevance=-0.5, age_days=0, source_confidence=0.5)
        assert score.relevance == 0.0  # Clamped

    def test_frequency_affects_score(self) -> None:
        scorer = ImportanceScorer()
        scorer.frequency_tracker.record_access("e5")
        scorer.frequency_tracker.record_access("e5")
        score_with = scorer.score_entry("e5", relevance=0.5, age_days=0, source_confidence=0.5)
        score_without = scorer.score_entry("e6", relevance=0.5, age_days=0, source_confidence=0.5)
        assert score_with.composite > score_without.composite

    def test_batch_scoring(self) -> None:
        scorer = ImportanceScorer()
        entries = [
            {"id": "a", "relevance": 0.9, "age_days": 0, "source_confidence": 0.8},
            {"id": "b", "relevance": 0.2, "age_days": 100, "source_confidence": 0.3},
            {"id": "c", "relevance": 0.5, "age_days": 10, "source_confidence": 0.6},
        ]
        scores = scorer.score_batch(entries)
        assert len(scores) == 3
        # Should be sorted descending by composite
        assert scores[0].composite >= scores[1].composite >= scores[2].composite

    def test_find_below_threshold(self) -> None:
        scorer = ImportanceScorer()
        scores = [
            MemoryScore(entry_id="a", composite=0.5),
            MemoryScore(entry_id="b", composite=0.1),
            MemoryScore(entry_id="c", composite=0.3),
        ]
        below = scorer.find_below_threshold(scores, threshold=0.2)
        assert len(below) == 1
        assert below[0].entry_id == "b"

    def test_stats(self) -> None:
        scorer = ImportanceScorer()
        s = scorer.stats()
        assert s["decay_strategy"] == "exponential"
        assert s["half_life_days"] == 30.0
        assert "weights" in s


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    def test_zero_half_life(self) -> None:
        scorer = ImportanceScorer(half_life_days=0.0)
        assert scorer.compute_recency(1.0) == 0.0

    def test_zero_max_age_linear(self) -> None:
        scorer = ImportanceScorer(decay_strategy=DecayStrategy.LINEAR, max_age_days=0.0)
        assert scorer.compute_recency(1.0) == 0.0

    def test_empty_batch(self) -> None:
        scorer = ImportanceScorer()
        assert scorer.score_batch([]) == []
