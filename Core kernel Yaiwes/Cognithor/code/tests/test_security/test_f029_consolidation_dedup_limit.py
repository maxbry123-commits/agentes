"""Tests fuer F-029: O(N^2) Consolidation Deduplication Batch-Limit.

Prueft dass:
  - MAX_FUZZY_ENTRIES Klassenvariable existiert und sinnvoll ist
  - Bei <= MAX_FUZZY_ENTRIES Eintraegen alle verglichen werden
  - Bei > MAX_FUZZY_ENTRIES Eintraegen nur die ersten MAX_FUZZY_ENTRIES verglichen werden
  - Phase-1 (exact hash) weiterhin unbegrenzt funktioniert
  - Bestehende Dedup-Logik nicht veraendert wurde
  - Source-Code das Limit enthaelt
"""

from __future__ import annotations

import inspect
import time

from cognithor.memory.consolidation import ContentDeduplicator

# ============================================================================
# MAX_FUZZY_ENTRIES Konfiguration
# ============================================================================


class TestMaxFuzzyEntriesConfig:
    """Prueft dass MAX_FUZZY_ENTRIES korrekt konfiguriert ist."""

    def test_class_attribute_exists(self) -> None:
        assert hasattr(ContentDeduplicator, "MAX_FUZZY_ENTRIES")

    def test_default_value_reasonable(self) -> None:
        """Standard-Limit ist zwischen 100 und 10000."""
        limit = ContentDeduplicator.MAX_FUZZY_ENTRIES
        assert 100 <= limit <= 10000

    def test_configurable_via_instance(self) -> None:
        """Limit kann pro Instanz ueberschrieben werden."""
        d = ContentDeduplicator()
        d.MAX_FUZZY_ENTRIES = 10
        assert d.MAX_FUZZY_ENTRIES == 10


# ============================================================================
# Batch-Limit Verhalten
# ============================================================================


def _make_entries(n: int, *, unique: bool = True) -> list[dict]:
    """Erzeugt n Eintraege mit eindeutigem oder identischem Content."""
    if unique:
        # Use hex strings to guarantee low n-gram overlap between entries
        import hashlib

        return [
            {"id": f"e{i}", "content": hashlib.sha256(f"seed-{i}".encode()).hexdigest()}
            for i in range(n)
        ]
    return [{"id": f"e{i}", "content": "identical content"} for i in range(n)]


class TestBatchLimitBehavior:
    """Prueft dass das Batch-Limit die O(N^2)-Schleife begrenzt."""

    def test_small_batch_fully_compared(self) -> None:
        """Weniger als MAX_FUZZY_ENTRIES: alle werden verglichen."""
        d = ContentDeduplicator(similarity_threshold=0.85)
        d.MAX_FUZZY_ENTRIES = 100
        entries = _make_entries(50, unique=True)
        # Keine Duplikate erwartet
        groups = d.find_duplicates(entries)
        assert len(groups) == 0

    def test_exact_limit_fully_compared(self) -> None:
        """Genau MAX_FUZZY_ENTRIES: alle werden verglichen."""
        d = ContentDeduplicator(similarity_threshold=0.85)
        d.MAX_FUZZY_ENTRIES = 20
        entries = _make_entries(20, unique=True)
        groups = d.find_duplicates(entries)
        assert len(groups) == 0

    def test_over_limit_truncated(self) -> None:
        """Mehr als MAX_FUZZY_ENTRIES: nur die ersten werden fuzzy verglichen."""
        d = ContentDeduplicator(similarity_threshold=0.85)
        d.MAX_FUZZY_ENTRIES = 5

        # 10 unique entries — only first 5 go through fuzzy phase
        entries = _make_entries(10, unique=True)
        # Add a near-duplicate pair beyond the limit
        entries[7]["content"] = entries[8]["content"] + " x"  # Very similar
        groups = d.find_duplicates(entries)
        # The pair at index 7/8 should NOT be found because they're beyond limit
        dup_ids = set()
        for g in groups:
            dup_ids.update(g.duplicate_ids)
        assert "e7" not in dup_ids and "e8" not in dup_ids

    def test_runtime_bounded_with_limit(self) -> None:
        """Mit Limit bleibt die Laufzeit bei grossem N konstant."""
        d = ContentDeduplicator(similarity_threshold=0.85)
        d.MAX_FUZZY_ENTRIES = 50

        # 2000 unique entries — without limit would be O(2000^2) = 4M comparisons
        entries = _make_entries(2000, unique=True)
        start = time.monotonic()
        d.find_duplicates(entries)
        elapsed_ms = (time.monotonic() - start) * 1000
        # Should complete in well under 5 seconds with the limit
        assert elapsed_ms < 5000, f"Took {elapsed_ms:.0f}ms — limit nicht wirksam?"


# ============================================================================
# Phase-1 (Exact Hash) unbegrenzt
# ============================================================================


class TestPhase1Unbounded:
    """Prueft dass Phase-1 (exact hash) nicht vom Limit betroffen ist."""

    def test_exact_duplicates_always_found(self) -> None:
        """Exact-hash Duplikate werden auch ueber dem Limit gefunden."""
        d = ContentDeduplicator()
        d.MAX_FUZZY_ENTRIES = 5

        # 20 Eintraege, davon 10 exakte Duplikate
        entries = []
        for i in range(10):
            entries.append({"id": f"orig{i}", "content": f"content {i}", "confidence": 0.9})
            entries.append({"id": f"dup{i}", "content": f"content {i}", "confidence": 0.5})

        groups = d.find_duplicates(entries)
        assert len(groups) == 10
        for g in groups:
            assert len(g.duplicate_ids) == 1
            assert g.similarity == 1.0

    def test_hash_dedup_removes_before_fuzzy(self) -> None:
        """Phase-1 entfernt Eintraege bevor Phase-2 das Limit anwendet."""
        d = ContentDeduplicator()
        d.MAX_FUZZY_ENTRIES = 10

        # 15 Eintraege: 5 exakte Duplikat-Paare + 5 einzigartige
        entries = []
        for i in range(5):
            entries.append({"id": f"a{i}", "content": f"dup content {i}", "confidence": 0.9})
            entries.append({"id": f"b{i}", "content": f"dup content {i}", "confidence": 0.5})
        for i in range(5):
            entries.append({"id": f"u{i}", "content": f"unique thing number {i} blah"})

        groups = d.find_duplicates(entries)
        # 5 exact groups found
        exact_groups = [g for g in groups if g.similarity == 1.0]
        assert len(exact_groups) == 5
        # remaining 5 unique entries < limit of 10, so all compared (no fuzzy matches)


# ============================================================================
# Bestehende Logik unveraendert
# ============================================================================


class TestExistingLogicPreserved:
    """Prueft dass die bestehende Dedup-Logik korrekt funktioniert."""

    def test_fuzzy_duplicates_found_within_limit(self) -> None:
        """Fuzzy-Duplikate innerhalb des Limits werden erkannt."""
        d = ContentDeduplicator(similarity_threshold=0.7)
        entries = [
            {"id": "a", "content": "the quick brown fox jumps over the lazy dog"},
            {"id": "b", "content": "the quick brown fox leaps over the lazy dog"},
            {"id": "c", "content": "something completely different with no overlap"},
        ]
        groups = d.find_duplicates(entries)
        # a and b should be fuzzy duplicates
        assert len(groups) == 1
        assert groups[0].canonical_id == "a"
        assert "b" in groups[0].duplicate_ids

    def test_ngram_similarity_symmetric(self) -> None:
        d = ContentDeduplicator()
        sim_ab = d.ngram_similarity("hello world", "hello world!")
        sim_ba = d.ngram_similarity("hello world!", "hello world")
        assert sim_ab == sim_ba

    def test_stats_updated(self) -> None:
        d = ContentDeduplicator()
        entries = _make_entries(10, unique=True)
        d.find_duplicates(entries)
        s = d.stats()
        assert s["scanned"] == 10


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf den Fix."""

    def test_max_fuzzy_entries_in_source(self) -> None:
        source = inspect.getsource(ContentDeduplicator)
        assert "MAX_FUZZY_ENTRIES" in source

    def test_limit_applied_in_find_duplicates(self) -> None:
        source = inspect.getsource(ContentDeduplicator.find_duplicates)
        assert "MAX_FUZZY_ENTRIES" in source

    def test_warning_logged_on_truncation(self) -> None:
        source = inspect.getsource(ContentDeduplicator.find_duplicates)
        assert "dedup_fuzzy_batch_limited" in source
