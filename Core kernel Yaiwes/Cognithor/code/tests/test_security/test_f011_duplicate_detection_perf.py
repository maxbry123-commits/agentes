"""Tests fuer F-011: O(N^2) Duplicate Detection muss begrenzt und optimiert sein.

Prueft dass:
  - MAX_ENTRIES Limit existiert und greift
  - Normalisierung gecacht wird (nicht redundant berechnet)
  - Pre-Filter ueber Wort-Set-Groesse funktioniert
  - Funktionale Korrektheit erhalten bleibt (exakte + near Duplicates)
  - Grosse Eingaben nicht zu O(N^2)-Explosion fuehren
  - _jaccard() korrekt arbeitet
"""

from __future__ import annotations

import time

import pytest

from cognithor.memory.integrity import DuplicateDetector, MemoryEntry


class TestMaxEntriesLimit:
    """Prueft dass das Batch-Limit greift."""

    def test_max_entries_exists(self) -> None:
        assert hasattr(DuplicateDetector, "MAX_ENTRIES")
        assert DuplicateDetector.MAX_ENTRIES > 0

    def test_large_input_truncated(self) -> None:
        """Bei mehr als MAX_ENTRIES Eintraegen wird gekuerzt."""
        detector = DuplicateDetector()
        n = detector.MAX_ENTRIES + 100
        entries = [
            MemoryEntry(entry_id=f"e{i}", content=f"unique content number {i}") for i in range(n)
        ]
        # Sollte nicht explodieren, sondern schnell zurueckkehren
        start = time.monotonic()
        groups = detector.detect(entries)
        elapsed = time.monotonic() - start
        assert isinstance(groups, list)
        # Darf nicht laenger als 30s dauern (bei 5000 Entries)
        assert elapsed < 30.0, f"detect() brauchte {elapsed:.1f}s — zu langsam"

    def test_entries_beyond_limit_uses_newest(self) -> None:
        """Bei Truncation werden die letzten (neuesten) Eintraege verwendet."""
        detector = DuplicateDetector()
        # Setze ein kleines Limit fuer den Test
        original_max = detector.MAX_ENTRIES
        DuplicateDetector.MAX_ENTRIES = 3
        try:
            entries = [
                MemoryEntry(entry_id="old1", content="the old entry one"),
                MemoryEntry(entry_id="old2", content="the old entry two"),
                MemoryEntry(entry_id="new1", content="the new entry one"),
                MemoryEntry(entry_id="dup1", content="the duplicate content here today"),
                MemoryEntry(entry_id="dup2", content="the duplicate content here today"),
            ]
            groups = detector.detect(entries)
            # Nur die letzten 3 Entries sollten verarbeitet werden
            # dup1 + dup2 sollten als Duplikat erkannt werden
            if groups:
                all_ids = [eid for g in groups for eid in g.entries]
                # old1 und old2 sollten nicht dabei sein (abgeschnitten)
                assert "old1" not in all_ids
                assert "old2" not in all_ids
        finally:
            DuplicateDetector.MAX_ENTRIES = original_max


class TestNormalizationCaching:
    """Prueft dass Normalisierung nicht redundant berechnet wird."""

    def test_normalize_called_once_per_entry(self) -> None:
        """Jeder Entry sollte genau einmal normalisiert werden."""
        import unittest.mock as mock

        detector = DuplicateDetector()
        entries = [
            MemoryEntry(entry_id="e1", content="the cat sat on the mat"),
            MemoryEntry(entry_id="e2", content="python programming language is great"),
            MemoryEntry(entry_id="e3", content="machine learning with python"),
        ]
        with mock.patch.object(
            DuplicateDetector, "_normalize", wraps=DuplicateDetector._normalize
        ) as mock_norm:
            detector.detect(entries)
            # Genau 3 Aufrufe (einer pro Entry), NICHT 3+2+1=6
            assert mock_norm.call_count == 3


class TestPreFilter:
    """Prueft den Pre-Filter ueber Wort-Set-Groesse."""

    def test_very_different_lengths_skipped(self) -> None:
        """Entries mit stark unterschiedlicher Wortanzahl werden uebersprungen."""
        detector = DuplicateDetector(similarity_threshold=0.85)
        # 2 Woerter vs 20 Woerter: Jaccard kann maximal 2/20 = 0.1 sein
        entries = [
            MemoryEntry(entry_id="short", content="hello world"),
            MemoryEntry(
                entry_id="long",
                content=(
                    "this is a very long entry with many many"
                    " words that are all different and unique"
                ),
            ),
        ]
        groups = detector.detect(entries)
        assert len(groups) == 0


class TestJaccardMethod:
    """Prueft die _jaccard() Hilfsmethode."""

    def test_identical_sets(self) -> None:
        words = {"the", "cat", "sat"}
        assert DuplicateDetector._jaccard(words, words) == 1.0

    def test_disjoint_sets(self) -> None:
        a = {"cat", "dog"}
        b = {"fish", "bird"}
        assert DuplicateDetector._jaccard(a, b) == 0.0

    def test_partial_overlap(self) -> None:
        a = {"the", "cat", "sat"}
        b = {"the", "cat", "ran"}
        # intersection = {"the", "cat"}, union = {"the", "cat", "sat", "ran"}
        assert DuplicateDetector._jaccard(a, b) == pytest.approx(0.5)

    def test_empty_sets(self) -> None:
        assert DuplicateDetector._jaccard(set(), {"a"}) == 0.0
        assert DuplicateDetector._jaccard({"a"}, set()) == 0.0
        assert DuplicateDetector._jaccard(set(), set()) == 0.0


class TestFunctionalCorrectness:
    """Prueft dass die Optimierungen die Korrektheit nicht beeintraechtigen."""

    def test_exact_duplicates_still_found(self) -> None:
        detector = DuplicateDetector()
        entries = [
            MemoryEntry(entry_id="e1", content="the quick brown fox jumps over the lazy dog"),
            MemoryEntry(entry_id="e2", content="the quick brown fox jumps over the lazy dog"),
        ]
        groups = detector.detect(entries)
        assert len(groups) == 1
        assert sorted(groups[0].entries) == ["e1", "e2"]

    def test_no_false_positives(self) -> None:
        detector = DuplicateDetector()
        entries = [
            MemoryEntry(entry_id="e1", content="apples oranges bananas grapes"),
            MemoryEntry(entry_id="e2", content="python java javascript rust"),
        ]
        groups = detector.detect(entries)
        assert len(groups) == 0

    def test_multiple_groups(self) -> None:
        detector = DuplicateDetector()
        entries = [
            MemoryEntry(entry_id="a1", content="the cat sat on the mat"),
            MemoryEntry(entry_id="a2", content="the cat sat on the mat"),
            MemoryEntry(
                entry_id="b1", content="python is great for data science and machine learning"
            ),
            MemoryEntry(
                entry_id="b2", content="python is great for data science and machine learning"
            ),
            MemoryEntry(entry_id="c1", content="unique entry with no duplicate"),
        ]
        groups = detector.detect(entries)
        assert len(groups) == 2

    def test_empty_input(self) -> None:
        detector = DuplicateDetector()
        groups = detector.detect([])
        assert groups == []

    def test_single_entry(self) -> None:
        detector = DuplicateDetector()
        entries = [MemoryEntry(entry_id="e1", content="only one entry")]
        groups = detector.detect(entries)
        assert groups == []


class TestPerformance:
    """Prueft dass die Optimierungen tatsaechlich schneller sind."""

    def test_1000_unique_entries_under_5s(self) -> None:
        """1000 einzigartige Entries muessen in unter 5 Sekunden verarbeitet werden."""
        detector = DuplicateDetector()
        entries = [
            MemoryEntry(
                entry_id=f"e{i}", content=f"unique content number {i} with extra words {i * 7}"
            )
            for i in range(1000)
        ]
        start = time.monotonic()
        groups = detector.detect(entries)
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"1000 Entries brauchten {elapsed:.1f}s"
        assert len(groups) == 0

    def test_500_with_duplicates_under_3s(self) -> None:
        """500 Entries (mit Duplikaten) muessen in unter 3 Sekunden verarbeitet werden."""
        detector = DuplicateDetector()
        entries = []
        for i in range(250):
            entries.append(
                MemoryEntry(entry_id=f"orig{i}", content=f"the entry about topic {i} is important")
            )
            entries.append(
                MemoryEntry(entry_id=f"dup{i}", content=f"the entry about topic {i} is important")
            )
        start = time.monotonic()
        groups = detector.detect(entries)
        elapsed = time.monotonic() - start
        assert elapsed < 3.0, f"500 Entries brauchten {elapsed:.1f}s"
        assert len(groups) == 250
