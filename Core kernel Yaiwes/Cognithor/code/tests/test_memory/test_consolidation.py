"""Tests for the Memory Consolidation Pipeline.

Covers content deduplication, memory budget, pipeline execution,
consolidation results, and edge cases.
"""

from __future__ import annotations

from cognithor.memory.consolidation import (
    ConsolidationPipeline,
    ConsolidationResult,
    ContentDeduplicator,
    MemoryBudgetManager,
    TierBudget,
)

# ============================================================================
# ContentDeduplicator
# ============================================================================


class TestContentDeduplicator:
    def setup_method(self) -> None:
        self.dedup = ContentDeduplicator(similarity_threshold=0.85)

    def test_content_hash_deterministic(self) -> None:
        h1 = self.dedup.content_hash("Hello World")
        h2 = self.dedup.content_hash("Hello World")
        assert h1 == h2

    def test_content_hash_case_insensitive(self) -> None:
        h1 = self.dedup.content_hash("Hello World")
        h2 = self.dedup.content_hash("hello world")
        assert h1 == h2

    def test_content_hash_whitespace_normalized(self) -> None:
        h1 = self.dedup.content_hash("Hello   World")
        h2 = self.dedup.content_hash("Hello World")
        assert h1 == h2

    def test_ngram_similarity_identical(self) -> None:
        sim = self.dedup.ngram_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_ngram_similarity_different(self) -> None:
        sim = self.dedup.ngram_similarity("hello world", "goodbye moon")
        assert sim < 0.5

    def test_ngram_similarity_empty(self) -> None:
        assert self.dedup.ngram_similarity("", "hello") == 0.0
        assert self.dedup.ngram_similarity("hello", "") == 0.0

    def test_ngram_similarity_similar(self) -> None:
        sim = self.dedup.ngram_similarity(
            "Berlin ist die Hauptstadt von Deutschland",
            "Berlin ist die Hauptstadt Deutschlands",
        )
        assert sim > 0.7

    def test_find_exact_duplicates(self) -> None:
        entries = [
            {"id": "a", "content": "Hello World", "confidence": 0.8},
            {"id": "b", "content": "Hello World", "confidence": 0.5},
        ]
        groups = self.dedup.find_duplicates(entries)
        assert len(groups) == 1
        assert groups[0].canonical_id == "a"  # Higher confidence
        assert "b" in groups[0].duplicate_ids

    def test_find_fuzzy_duplicates(self) -> None:
        entries = [
            {
                "id": "a",
                "content": (
                    "Berlin ist die Hauptstadt von Deutschland und hat viele Sehenswuerdigkeiten."
                ),
            },
            {
                "id": "b",
                "content": (
                    "Berlin ist die Hauptstadt Deutschlands und hat viele Sehenswuerdigkeiten."
                ),
            },
        ]
        dedup = ContentDeduplicator(similarity_threshold=0.80)
        groups = dedup.find_duplicates(entries)
        assert len(groups) >= 1

    def test_no_duplicates(self) -> None:
        entries = [
            {"id": "a", "content": "Completely different text about apples."},
            {"id": "b", "content": "Totally unrelated content about zebras."},
        ]
        groups = self.dedup.find_duplicates(entries)
        assert len(groups) == 0

    def test_empty_entries(self) -> None:
        groups = self.dedup.find_duplicates([])
        assert groups == []

    def test_single_entry(self) -> None:
        entries = [{"id": "a", "content": "Only one entry"}]
        groups = self.dedup.find_duplicates(entries)
        assert groups == []

    def test_duplicate_rate(self) -> None:
        dedup = ContentDeduplicator()
        entries = [
            {"id": "a", "content": "Same text", "confidence": 0.8},
            {"id": "b", "content": "Same text", "confidence": 0.5},
            {"id": "c", "content": "Different text entirely"},
        ]
        dedup.find_duplicates(entries)
        assert dedup.duplicate_rate > 0

    def test_stats(self) -> None:
        s = self.dedup.stats()
        assert "scanned" in s
        assert "similarity_threshold" in s


# ============================================================================
# TierBudget
# ============================================================================


class TestTierBudget:
    def test_utilization(self) -> None:
        b = TierBudget(tier="episodic", max_tokens=100, current_tokens=75)
        assert b.utilization == 0.75

    def test_over_budget(self) -> None:
        b = TierBudget(tier="episodic", max_tokens=100, current_tokens=150)
        assert b.over_budget is True

    def test_under_budget(self) -> None:
        b = TierBudget(tier="episodic", max_tokens=100, current_tokens=50)
        assert b.over_budget is False

    def test_remaining_tokens(self) -> None:
        b = TierBudget(tier="episodic", max_tokens=100, current_tokens=60)
        assert b.remaining_tokens == 40

    def test_remaining_tokens_over_budget(self) -> None:
        b = TierBudget(tier="episodic", max_tokens=100, current_tokens=150)
        assert b.remaining_tokens == 0

    def test_zero_max(self) -> None:
        b = TierBudget(tier="x", max_tokens=0, current_tokens=0)
        assert b.utilization == 0.0


# ============================================================================
# MemoryBudgetManager
# ============================================================================


class TestMemoryBudgetManager:
    def test_default_budgets(self) -> None:
        mgr = MemoryBudgetManager()
        b = mgr.get_budget("episodic")
        assert b is not None
        assert b.max_tokens == 100000

    def test_custom_budgets(self) -> None:
        mgr = MemoryBudgetManager(budgets={"episodic": 5000, "semantic": 3000})
        assert mgr.get_budget("episodic").max_tokens == 5000
        assert mgr.get_budget("semantic").max_tokens == 3000

    def test_unknown_tier(self) -> None:
        mgr = MemoryBudgetManager()
        assert mgr.get_budget("unknown_tier") is None

    def test_update_usage(self) -> None:
        mgr = MemoryBudgetManager()
        mgr.update_usage("episodic", 80000, 500)
        b = mgr.get_budget("episodic")
        assert b.current_tokens == 80000
        assert b.entry_count == 500

    def test_over_budget_tiers(self) -> None:
        mgr = MemoryBudgetManager(budgets={"episodic": 100, "semantic": 1000})
        mgr.update_usage("episodic", 200, 10)
        mgr.update_usage("semantic", 500, 5)
        over = mgr.over_budget_tiers()
        assert "episodic" in over
        assert "semantic" not in over

    def test_tokens_to_free(self) -> None:
        mgr = MemoryBudgetManager(budgets={"episodic": 100})
        mgr.update_usage("episodic", 150, 10)
        assert mgr.tokens_to_free("episodic") == 50

    def test_tokens_to_free_under_budget(self) -> None:
        mgr = MemoryBudgetManager(budgets={"episodic": 100})
        mgr.update_usage("episodic", 50, 5)
        assert mgr.tokens_to_free("episodic") == 0

    def test_stats(self) -> None:
        mgr = MemoryBudgetManager()
        s = mgr.stats()
        assert "episodic" in s
        assert "utilization" in s["episodic"]


# ============================================================================
# ConsolidationResult
# ============================================================================


class TestConsolidationResult:
    def test_to_dict(self) -> None:
        r = ConsolidationResult(
            timestamp="2026-03-04T12:00:00Z",
            entries_scanned=100,
            duplicates_found=10,
            duplicates_merged=10,
            entries_archived=5,
            tokens_freed=500,
            duration_ms=42.5,
        )
        d = r.to_dict()
        assert d["entries_scanned"] == 100
        assert d["tokens_freed"] == 500
        assert d["duration_ms"] == 42.5


# ============================================================================
# ConsolidationPipeline
# ============================================================================


class TestConsolidationPipeline:
    def test_empty_entries(self) -> None:
        pipeline = ConsolidationPipeline()
        result = pipeline.run([])
        assert result.entries_scanned == 0
        assert result.duplicates_found == 0

    def test_no_duplicates(self) -> None:
        pipeline = ConsolidationPipeline()
        entries = [
            {
                "id": "a",
                "content": "Apples are red fruits",
                "age_days": 5,
                "source_confidence": 0.8,
                "token_count": 50,
            },
            {
                "id": "b",
                "content": "Bananas are yellow fruits",
                "age_days": 3,
                "source_confidence": 0.7,
                "token_count": 50,
            },
        ]
        result = pipeline.run(entries)
        assert result.entries_scanned == 2
        assert result.duplicates_merged == 0

    def test_with_duplicates(self) -> None:
        pipeline = ConsolidationPipeline()
        entries = [
            {
                "id": "a",
                "content": "Same content here",
                "age_days": 5,
                "source_confidence": 0.8,
                "token_count": 50,
            },
            {
                "id": "b",
                "content": "Same content here",
                "age_days": 3,
                "source_confidence": 0.5,
                "token_count": 50,
            },
            {
                "id": "c",
                "content": "Different content entirely",
                "age_days": 1,
                "source_confidence": 0.9,
                "token_count": 50,
            },
        ]
        result = pipeline.run(entries)
        assert result.duplicates_found >= 1
        assert result.duplicates_merged >= 1

    def test_archives_low_score_entries(self) -> None:
        pipeline = ConsolidationPipeline(archive_threshold=0.5)
        entries = [
            {
                "id": "old",
                "content": "Very old and irrelevant",
                "age_days": 500,
                "source_confidence": 0.1,
                "token_count": 200,
            },
            {
                "id": "new",
                "content": "Fresh and relevant",
                "age_days": 0,
                "source_confidence": 0.9,
                "token_count": 100,
            },
        ]
        result = pipeline.run(entries)
        assert result.entries_archived >= 1

    def test_summarization_candidates(self) -> None:
        pipeline = ConsolidationPipeline(summarize_age_days=30.0)
        entries = [
            {
                "id": "old",
                "content": "An old entry",
                "age_days": 45,
                "source_confidence": 0.7,
                "token_count": 100,
            },
            {
                "id": "new",
                "content": "A fresh entry",
                "age_days": 2,
                "source_confidence": 0.8,
                "token_count": 100,
            },
        ]
        result = pipeline.run(entries)
        assert result.entries_summarized >= 1

    def test_budget_updated(self) -> None:
        pipeline = ConsolidationPipeline()
        entries = [
            {
                "id": "a",
                "content": "Entry A",
                "age_days": 0,
                "source_confidence": 0.8,
                "token_count": 200,
            },
            {
                "id": "b",
                "content": "Entry B",
                "age_days": 0,
                "source_confidence": 0.7,
                "token_count": 300,
            },
        ]
        pipeline.run(entries, tier="episodic")
        budget = pipeline.budget_manager.get_budget("episodic")
        assert budget is not None
        assert budget.current_tokens > 0

    def test_history_recorded(self) -> None:
        pipeline = ConsolidationPipeline()
        pipeline.run([{"id": "a", "content": "X", "age_days": 0, "source_confidence": 0.5}])
        pipeline.run([{"id": "b", "content": "Y", "age_days": 0, "source_confidence": 0.5}])
        assert len(pipeline.history) == 2

    def test_duration_positive(self) -> None:
        pipeline = ConsolidationPipeline()
        result = pipeline.run(
            [{"id": "a", "content": "X", "age_days": 0, "source_confidence": 0.5}]
        )
        assert result.duration_ms >= 0

    def test_stats(self) -> None:
        pipeline = ConsolidationPipeline()
        pipeline.run([{"id": "a", "content": "X", "age_days": 0, "source_confidence": 0.5}])
        s = pipeline.stats()
        assert s["runs"] == 1
        assert "dedup_stats" in s
        assert "scorer_stats" in s
        assert "budget_stats" in s

    def test_tokens_freed_from_archived(self) -> None:
        pipeline = ConsolidationPipeline(archive_threshold=0.5)
        entries = [
            {
                "id": "trash",
                "content": "Useless",
                "age_days": 999,
                "source_confidence": 0.0,
                "token_count": 500,
            },
        ]
        result = pipeline.run(entries)
        assert result.tokens_freed >= 500

    def test_custom_tier(self) -> None:
        pipeline = ConsolidationPipeline()
        entries = [
            {"id": "a", "content": "X", "age_days": 0, "source_confidence": 0.5, "token_count": 100}
        ]
        pipeline.run(entries, tier="semantic")
        budget = pipeline.budget_manager.get_budget("semantic")
        assert budget.current_tokens > 0
