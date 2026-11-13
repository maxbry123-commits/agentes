"""Tests for FAISS-backed VectorStore."""

from __future__ import annotations

import numpy as np
import pytest

from mmem.indexing.vector_store import DEFAULT_INDEX_NAMES, VectorStore

DIM = 8


def _random_vecs(n: int, dim: int = DIM) -> np.ndarray:
    """Generate *n* L2-normalised random vectors."""
    vecs = np.random.randn(n, dim).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


class TestInit:
    def test_default_indexes(self):
        store = VectorStore(dimension=DIM)
        assert store.dimension == DIM
        assert set(store.index_names) == set(DEFAULT_INDEX_NAMES)
        for name in DEFAULT_INDEX_NAMES:
            assert store.has_index(name)
            assert store.count(name) == 0

    def test_custom_indexes(self):
        store = VectorStore(dimension=DIM, index_names=["a", "b"])
        assert store.index_names == ["a", "b"]
        assert store.has_index("a")
        assert not store.has_index("entity")


class TestHasIndex:
    def test_returns_true_for_registered(self):
        store = VectorStore(dimension=DIM, index_names=["x"])
        assert store.has_index("x") is True

    def test_returns_false_for_unknown(self):
        store = VectorStore(dimension=DIM, index_names=["x"])
        assert store.has_index("bogus") is False


class TestAdd:
    def test_add_vectors(self):
        store = VectorStore(dimension=DIM)
        vecs = _random_vecs(3)
        store.add("entity", ["e1", "e2", "e3"], vecs)
        assert store.count("entity") == 3

    def test_add_increments(self):
        store = VectorStore(dimension=DIM)
        store.add("entity", ["e1"], _random_vecs(1))
        store.add("entity", ["e2"], _random_vecs(1))
        assert store.count("entity") == 2

    def test_add_empty_is_noop(self):
        store = VectorStore(dimension=DIM)
        store.add("entity", [], np.empty((0, DIM), dtype=np.float32))
        assert store.count("entity") == 0

    def test_add_rejects_unknown_index(self):
        store = VectorStore(dimension=DIM)
        with pytest.raises(KeyError, match="Unknown index"):
            store.add("nonexistent", ["x"], _random_vecs(1))

    def test_add_rejects_dimension_mismatch(self):
        store = VectorStore(dimension=DIM)
        bad_vecs = np.random.randn(1, DIM + 1).astype(np.float32)
        with pytest.raises(ValueError, match="dimension mismatch"):
            store.add("entity", ["x"], bad_vecs)

    def test_add_rejects_row_count_mismatch(self):
        store = VectorStore(dimension=DIM)
        with pytest.raises(ValueError, match="Expected 2 rows"):
            store.add("entity", ["a", "b"], _random_vecs(3))

    def test_add_single_vector_1d(self):
        store = VectorStore(dimension=DIM)
        vec = _random_vecs(1).squeeze()
        assert vec.ndim == 1
        store.add("entity", ["e1"], vec)
        assert store.count("entity") == 1


class TestSearch:
    def test_search_returns_correct_ids(self):
        store = VectorStore(dimension=DIM)
        vecs = _random_vecs(5)
        store.add("entity", ["a", "b", "c", "d", "e"], vecs)

        results = store.search("entity", vecs[2], top_k=3)
        assert len(results) == 3
        assert results[0][0] == "c"
        assert results[0][1] == pytest.approx(1.0, abs=1e-4)

    def test_search_empty_index_returns_empty(self):
        store = VectorStore(dimension=DIM)
        results = store.search("entity", _random_vecs(1).squeeze(), top_k=5)
        assert results == []

    def test_search_top_k_larger_than_index(self):
        store = VectorStore(dimension=DIM)
        store.add("entity", ["a", "b"], _random_vecs(2))
        results = store.search("entity", _random_vecs(1).squeeze(), top_k=100)
        assert len(results) == 2

    def test_search_rejects_unknown_index(self):
        store = VectorStore(dimension=DIM)
        with pytest.raises(KeyError, match="Unknown index"):
            store.search("bogus", _random_vecs(1).squeeze())

    def test_search_rejects_dimension_mismatch(self):
        store = VectorStore(dimension=DIM)
        store.add("entity", ["a"], _random_vecs(1))
        bad_query = np.random.randn(DIM + 1).astype(np.float32)
        with pytest.raises(ValueError, match="Query dimension mismatch"):
            store.search("entity", bad_query)

    def test_search_scores_descending(self):
        store = VectorStore(dimension=DIM)
        vecs = _random_vecs(10)
        ids = [f"n{i}" for i in range(10)]
        store.add("entity", ids, vecs)

        results = store.search("entity", vecs[0], top_k=10)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)


class TestSearchMulti:
    def test_returns_all_indexes(self):
        store = VectorStore(dimension=DIM, index_names=["a", "b", "c"])
        store.add("a", ["x"], _random_vecs(1))

        query = _random_vecs(1).squeeze()
        results = store.search_multi(query, top_k=5)
        assert set(results.keys()) == {"a", "b", "c"}
        assert len(results["a"]) == 1
        assert results["b"] == []
        assert results["c"] == []


class TestCount:
    def test_count_rejects_unknown_index(self):
        store = VectorStore(dimension=DIM)
        with pytest.raises(KeyError, match="Unknown index"):
            store.count("nope")


class TestPersistence:
    def test_save_and_load_round_trip(self, tmp_path):
        store = VectorStore(dimension=DIM)
        vecs_entity = _random_vecs(3)
        vecs_episode = _random_vecs(2)
        store.add("entity", ["e1", "e2", "e3"], vecs_entity)
        store.add("episode", ["ep1", "ep2"], vecs_episode)

        store.save_dir(tmp_path / "vs")
        loaded = VectorStore.load_dir(tmp_path / "vs")

        assert loaded.dimension == DIM
        assert set(loaded.index_names) == set(DEFAULT_INDEX_NAMES)
        assert loaded.count("entity") == 3
        assert loaded.count("episode") == 2

        r1 = store.search("entity", vecs_entity[0], top_k=3)
        r2 = loaded.search("entity", vecs_entity[0], top_k=3)
        assert [rid for rid, _ in r1] == [rid for rid, _ in r2]

    def test_load_missing_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="metadata.json"):
            VectorStore.load_dir(tmp_path / "nonexistent")

    def test_save_load_empty_store(self, tmp_path):
        store = VectorStore(dimension=DIM)
        store.save_dir(tmp_path / "empty")
        loaded = VectorStore.load_dir(tmp_path / "empty")
        for name in DEFAULT_INDEX_NAMES:
            assert loaded.count(name) == 0

    def test_save_load_custom_indexes(self, tmp_path):
        store = VectorStore(dimension=DIM, index_names=["alpha", "beta"])
        store.add("alpha", ["a1", "a2"], _random_vecs(2))
        store.save_dir(tmp_path / "custom")

        loaded = VectorStore.load_dir(tmp_path / "custom")
        assert loaded.index_names == ["alpha", "beta"]
        assert loaded.count("alpha") == 2
        assert loaded.count("beta") == 0
        assert not loaded.has_index("entity")


class TestRepr:
    def test_repr_shows_counts(self):
        store = VectorStore(dimension=DIM, index_names=["a", "b"])
        store.add("a", ["x", "y"], _random_vecs(2))
        r = repr(store)
        assert "dim=8" in r
        assert "total_vectors=2" in r
