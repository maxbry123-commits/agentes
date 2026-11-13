"""Tests für optimierte Embedding-Zugriffe im MemoryIndex.

Validiert:
- get_embeddings_by_hashes() lädt nur angeforderte Hashes
- get_embedding_hashes() gibt nur Hashes ohne Vektoren
- Batching bei >900 Hashes (SQLite-Limit)
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING

import pytest

from cognithor.memory.indexer import MemoryIndex

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def index(tmp_path: Path) -> MemoryIndex:
    """MemoryIndex mit temporärer DB."""
    idx = MemoryIndex(tmp_path / "test.db")
    return idx


def _make_vector(dim: int = 4, seed: float = 1.0) -> bytes:
    """Erzeugt einen serialisierten Vektor."""
    return struct.pack(f"{dim}f", *[seed * (i + 1) for i in range(dim)])


_INSERT_EMBEDDING = (
    "INSERT INTO embeddings"
    " (content_hash, vector, model_name, dimensions, created_at)"
    " VALUES (?, ?, 'test', 4, 0.0)"
)


class TestGetEmbeddingsByHashes:
    """Testet die optimierte Hash-basierte Embedding-Abfrage."""

    def test_empty_hashes_returns_empty(self, index: MemoryIndex) -> None:
        result = index.get_embeddings_by_hashes(set())
        assert result == {}

    def test_returns_only_requested(self, index: MemoryIndex) -> None:
        """Gibt nur die angeforderten Hashes zurück."""
        # 3 Embeddings speichern
        for i in range(3):
            index.conn.execute(
                _INSERT_EMBEDDING,
                (f"hash_{i}", _make_vector(seed=float(i))),
            )
        index.conn.commit()

        # Nur 1 davon abfragen
        result = index.get_embeddings_by_hashes({"hash_1"})
        assert len(result) == 1
        assert "hash_1" in result
        assert "hash_0" not in result
        assert "hash_2" not in result

    def test_missing_hashes_not_in_result(self, index: MemoryIndex) -> None:
        """Nicht existierende Hashes werden ignoriert."""
        index.conn.execute(
            _INSERT_EMBEDDING,
            ("existing", _make_vector()),
        )
        index.conn.commit()

        result = index.get_embeddings_by_hashes({"existing", "missing_1", "missing_2"})
        assert len(result) == 1
        assert "existing" in result

    def test_batching_over_900(self, index: MemoryIndex) -> None:
        """Mehr als 900 Hashes werden korrekt in Batches verarbeitet."""
        # 1000 Embeddings einfügen
        for i in range(1000):
            index.conn.execute(
                _INSERT_EMBEDDING,
                (f"h_{i}", _make_vector(seed=float(i))),
            )
        index.conn.commit()

        # Alle 1000 abfragen (erzwingt 2 Batches: 900 + 100)
        all_hashes = {f"h_{i}" for i in range(1000)}
        result = index.get_embeddings_by_hashes(all_hashes)
        assert len(result) == 1000

    def test_vectors_are_correct(self, index: MemoryIndex) -> None:
        """Zurückgegebene Vektoren stimmen mit gespeicherten überein."""
        vec = _make_vector(dim=4, seed=3.14)
        index.conn.execute(
            _INSERT_EMBEDDING,
            ("pi_hash", vec),
        )
        index.conn.commit()

        result = index.get_embeddings_by_hashes({"pi_hash"})
        stored = result["pi_hash"]
        expected = list(struct.unpack("4f", vec))
        for a, b in zip(stored, expected, strict=False):
            assert abs(a - b) < 1e-5


class TestGetEmbeddingHashes:
    """Testet get_embedding_hashes() — nur Hashes, keine Vektoren."""

    def test_empty_db_returns_empty(self, index: MemoryIndex) -> None:
        result = index.get_embedding_hashes()
        assert result == set()

    def test_returns_all_hashes(self, index: MemoryIndex) -> None:
        for i in range(5):
            index.conn.execute(
                _INSERT_EMBEDDING,
                (f"hash_{i}", _make_vector()),
            )
        index.conn.commit()

        result = index.get_embedding_hashes()
        assert result == {f"hash_{i}" for i in range(5)}

    def test_returns_set_type(self, index: MemoryIndex) -> None:
        result = index.get_embedding_hashes()
        assert isinstance(result, set)
