"""Tests für graph_traverse() — Zyklen-sichere BFS im Wissens-Graphen.

Validiert:
- Einfache lineare Traversierung (A→B→C)
- Zyklische Graphen (A→B→A) terminieren
- Dreiecke (A→B→C→A) terminieren
- max_depth wird eingehalten
- Dichte Graphen (K5 Clique) terminieren
- Start-Entität ist nicht im Ergebnis
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from cognithor.memory.indexer import MemoryIndex

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def index(tmp_path: Path) -> MemoryIndex:
    idx = MemoryIndex(tmp_path / "graph_test.db")
    return idx


def _add_entity(idx: MemoryIndex, eid: str) -> None:
    now = datetime.now(UTC).timestamp()
    idx.conn.execute(
        "INSERT OR IGNORE INTO entities"
        " (id, type, name, source_file, created_at, updated_at, confidence)"
        " VALUES (?, 'person', ?, 'test', ?, ?, 1.0)",
        (eid, eid, now, now),
    )
    idx.conn.commit()


def _add_relation(idx: MemoryIndex, source: str, target: str) -> None:
    import uuid

    idx.conn.execute(
        "INSERT INTO relations"
        " (id, source_entity, relation_type, target_entity,"
        " source_file, created_at, confidence)"
        " VALUES (?, ?, 'knows', ?, 'test', ?, 1.0)",
        (uuid.uuid4().hex, source, target, datetime.now(UTC).timestamp()),
    )
    idx.conn.commit()


class TestGraphTraverseCycles:
    """Testet dass zyklische Graphen korrekt terminieren."""

    def test_simple_cycle_a_b_a(self, index: MemoryIndex) -> None:
        """A↔B Zyklus terminiert."""
        _add_entity(index, "A")
        _add_entity(index, "B")
        _add_relation(index, "A", "B")
        _add_relation(index, "B", "A")

        result = index.graph_traverse("A", max_depth=5)
        names = {e.id for e in result}
        assert names == {"B"}

    def test_triangle_cycle(self, index: MemoryIndex) -> None:
        """A→B→C→A Dreieck terminiert."""
        for eid in ("A", "B", "C"):
            _add_entity(index, eid)
        _add_relation(index, "A", "B")
        _add_relation(index, "B", "C")
        _add_relation(index, "C", "A")

        result = index.graph_traverse("A", max_depth=10)
        names = {e.id for e in result}
        assert names == {"B", "C"}

    def test_dense_clique_k5(self, index: MemoryIndex) -> None:
        """K5 (vollständiger Graph mit 5 Knoten) terminiert schnell."""
        nodes = ["K1", "K2", "K3", "K4", "K5"]
        for n in nodes:
            _add_entity(index, n)
        for i, a in enumerate(nodes):
            for b in nodes[i + 1 :]:
                _add_relation(index, a, b)

        result = index.graph_traverse("K1", max_depth=3)
        names = {e.id for e in result}
        assert names == {"K2", "K3", "K4", "K5"}

    def test_self_loop(self, index: MemoryIndex) -> None:
        """Selbst-Referenz (A→A) terminiert."""
        _add_entity(index, "A")
        _add_relation(index, "A", "A")

        result = index.graph_traverse("A", max_depth=5)
        assert result == []


class TestGraphTraverseDepth:
    """Testet max_depth Begrenzung."""

    def test_depth_1_only_direct_neighbors(self, index: MemoryIndex) -> None:
        """Depth=1 findet nur direkte Nachbarn."""
        for eid in ("A", "B", "C", "D"):
            _add_entity(index, eid)
        _add_relation(index, "A", "B")
        _add_relation(index, "B", "C")
        _add_relation(index, "C", "D")

        result = index.graph_traverse("A", max_depth=1)
        names = {e.id for e in result}
        assert names == {"B"}

    def test_depth_2_finds_two_hops(self, index: MemoryIndex) -> None:
        """Depth=2 findet 2-Hop-Nachbarn."""
        for eid in ("A", "B", "C", "D"):
            _add_entity(index, eid)
        _add_relation(index, "A", "B")
        _add_relation(index, "B", "C")
        _add_relation(index, "C", "D")

        result = index.graph_traverse("A", max_depth=2)
        names = {e.id for e in result}
        assert names == {"B", "C"}

    def test_depth_0_returns_empty(self, index: MemoryIndex) -> None:
        """Depth=0 findet nichts."""
        _add_entity(index, "A")
        _add_entity(index, "B")
        _add_relation(index, "A", "B")

        result = index.graph_traverse("A", max_depth=0)
        assert result == []


class TestGraphTraverseBasic:
    """Grundlegende Traversierungs-Tests."""

    def test_no_relations_returns_empty(self, index: MemoryIndex) -> None:
        """Isolierte Entität hat keine Nachbarn."""
        _add_entity(index, "lonely")
        result = index.graph_traverse("lonely", max_depth=3)
        assert result == []

    def test_start_not_in_result(self, index: MemoryIndex) -> None:
        """Start-Entität ist nicht im Ergebnis."""
        _add_entity(index, "A")
        _add_entity(index, "B")
        _add_relation(index, "A", "B")

        result = index.graph_traverse("A", max_depth=2)
        ids = {e.id for e in result}
        assert "A" not in ids

    def test_nonexistent_entity_returns_empty(self, index: MemoryIndex) -> None:
        """Nicht existierende Start-Entität gibt leere Liste."""
        result = index.graph_traverse("nonexistent", max_depth=3)
        assert result == []

    def test_bidirectional_traversal(self, index: MemoryIndex) -> None:
        """Findet Nachbarn in beiden Richtungen."""
        for eid in ("A", "B", "C"):
            _add_entity(index, eid)
        _add_relation(index, "B", "A")  # B→A (A ist Ziel)
        _add_relation(index, "A", "C")  # A→C (A ist Quelle)

        result = index.graph_traverse("A", max_depth=1)
        names = {e.id for e in result}
        assert names == {"B", "C"}
