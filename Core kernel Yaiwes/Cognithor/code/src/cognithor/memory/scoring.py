"""Memory Importance Scoring — ranks memory entries by value.

Composite score: Relevance × Recency × Frequency × Source Trust.

Each factor is normalized to [0, 1]:
- **Relevance**: semantic similarity to the current query (if available)
- **Recency**: exponential decay with configurable half-life
- **Frequency**: how often the entry has been retrieved
- **Source Trust**: confidence from extraction source

Architecture: §8.4 (Memory Consolidation Pipeline)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# Score components
# ---------------------------------------------------------------------------


class DecayStrategy(StrEnum):
    """How memory entries age over time."""

    EXPONENTIAL = "exponential"  # exp(-age / half_life)
    LINEAR = "linear"  # max(0, 1 - age / max_age)
    STEP = "step"  # 1.0 if age < threshold else low_value
    NONE = "none"  # Always 1.0


@dataclass(frozen=True)
class ScoringWeights:
    """Configurable weights for the composite score."""

    relevance: float = 0.40
    recency: float = 0.30
    frequency: float = 0.15
    source_trust: float = 0.15

    def __post_init__(self) -> None:
        total = self.relevance + self.recency + self.frequency + self.source_trust
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")


@dataclass
class MemoryScore:
    """Computed importance score for a memory entry."""

    entry_id: str
    composite: float = 0.0
    relevance: float = 0.0
    recency: float = 0.0
    frequency: float = 0.0
    source_trust: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def above_threshold(self) -> bool:
        """Whether this entry is above the default archival threshold."""
        return self.composite >= 0.2


# ---------------------------------------------------------------------------
# Frequency tracker (in-memory, lightweight)
# ---------------------------------------------------------------------------


class FrequencyTracker:
    """Tracks how often each entry is accessed."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self._max_count: int = 0

    def record_access(self, entry_id: str) -> None:
        """Record one access of an entry."""
        self._counts[entry_id] = self._counts.get(entry_id, 0) + 1
        if self._counts[entry_id] > self._max_count:
            self._max_count = self._counts[entry_id]

    def get_normalized(self, entry_id: str) -> float:
        """Get frequency score in [0, 1]."""
        if self._max_count == 0:
            return 0.0
        return self._counts.get(entry_id, 0) / self._max_count

    def get_count(self, entry_id: str) -> int:
        return self._counts.get(entry_id, 0)

    @property
    def total_entries(self) -> int:
        return len(self._counts)

    @property
    def total_accesses(self) -> int:
        return sum(self._counts.values())


# ---------------------------------------------------------------------------
# Importance Scorer
# ---------------------------------------------------------------------------


class ImportanceScorer:
    """Computes composite importance scores for memory entries.

    Score = w_relevance * relevance
          + w_recency * recency_decay(age)
          + w_frequency * freq_normalized
          + w_source_trust * source_confidence
    """

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        decay_strategy: DecayStrategy = DecayStrategy.EXPONENTIAL,
        half_life_days: float = 30.0,
        max_age_days: float = 365.0,
        step_threshold_days: float = 90.0,
        step_low_value: float = 0.2,
    ) -> None:
        self.weights = weights or ScoringWeights()
        self.decay_strategy = decay_strategy
        self.half_life_days = half_life_days
        self.max_age_days = max_age_days
        self.step_threshold_days = step_threshold_days
        self.step_low_value = step_low_value
        self._frequency = FrequencyTracker()

    @property
    def frequency_tracker(self) -> FrequencyTracker:
        return self._frequency

    def compute_recency(self, age_days: float) -> float:
        """Compute recency score based on decay strategy."""
        if age_days < 0:
            age_days = 0.0

        if self.decay_strategy == DecayStrategy.EXPONENTIAL:
            return math.exp(-age_days / self.half_life_days) if self.half_life_days > 0 else 0.0
        elif self.decay_strategy == DecayStrategy.LINEAR:
            return max(0.0, 1.0 - age_days / self.max_age_days) if self.max_age_days > 0 else 0.0
        elif self.decay_strategy == DecayStrategy.STEP:
            return 1.0 if age_days < self.step_threshold_days else self.step_low_value
        else:  # NONE
            return 1.0

    def score_entry(
        self,
        entry_id: str,
        *,
        relevance: float = 0.5,
        age_days: float = 0.0,
        source_confidence: float = 0.5,
    ) -> MemoryScore:
        """Compute the composite importance score for a single entry.

        Args:
            entry_id: Unique identifier for the memory entry.
            relevance: Query relevance score [0, 1].
            age_days: How old the entry is in days.
            source_confidence: Extraction confidence [0, 1].

        Returns:
            MemoryScore with all components.
        """
        recency = self.compute_recency(age_days)
        frequency = self._frequency.get_normalized(entry_id)

        composite = (
            self.weights.relevance * min(max(relevance, 0.0), 1.0)
            + self.weights.recency * recency
            + self.weights.frequency * frequency
            + self.weights.source_trust * min(max(source_confidence, 0.0), 1.0)
        )

        return MemoryScore(
            entry_id=entry_id,
            composite=round(composite, 6),
            relevance=round(min(max(relevance, 0.0), 1.0), 6),
            recency=round(recency, 6),
            frequency=round(frequency, 6),
            source_trust=round(min(max(source_confidence, 0.0), 1.0), 6),
        )

    def score_batch(
        self,
        entries: list[dict[str, Any]],
    ) -> list[MemoryScore]:
        """Score multiple entries. Each dict needs: id, relevance, age_days, source_confidence.

        Returns sorted by composite score (descending).
        """
        scores = []
        for entry in entries:
            score = self.score_entry(
                entry_id=entry["id"],
                relevance=entry.get("relevance", 0.5),
                age_days=entry.get("age_days", 0.0),
                source_confidence=entry.get("source_confidence", 0.5),
            )
            scores.append(score)
        scores.sort(key=lambda s: s.composite, reverse=True)
        return scores

    def find_below_threshold(
        self,
        scores: list[MemoryScore],
        threshold: float = 0.2,
    ) -> list[MemoryScore]:
        """Find entries below the archival threshold."""
        return [s for s in scores if s.composite < threshold]

    def stats(self) -> dict[str, Any]:
        """Return scorer statistics."""
        return {
            "decay_strategy": self.decay_strategy.value,
            "half_life_days": self.half_life_days,
            "weights": {
                "relevance": self.weights.relevance,
                "recency": self.weights.recency,
                "frequency": self.weights.frequency,
                "source_trust": self.weights.source_trust,
            },
            "tracked_entries": self._frequency.total_entries,
            "total_accesses": self._frequency.total_accesses,
        }
