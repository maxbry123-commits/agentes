"""Tests for Phase 1: anchor discovery."""

import numpy as np
import pytest

from mmem.config import RetrievalConfig
from mmem.indexing.vector_store import VectorStore
from mmem.retrieval.anchor_discovery import AnchorResult, discover_anchors
from mmem.retrieval.query_preprocessor import PreprocessedQuery

DIM = 8


class FakeEmbedder:
    def embed(self, text: str) -> np.ndarray:
        vec = np.ones(DIM, dtype=np.float32) / np.sqrt(DIM)
        return vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.embed(t) for t in texts])


def _make_pq(query: str = "Alice career") -> PreprocessedQuery:
    return PreprocessedQuery(original=query, vector_query=query)


def _add_vec(vs: VectorStore, index_name: str, item_id: str, vec: np.ndarray | None = None):
    if vec is None:
        vec = np.ones(DIM, dtype=np.float32) / np.sqrt(DIM)
    vs.add(index_name, [item_id], vec.reshape(1, -1))


class TestBasicSearch:
    def test_returns_node_distances(self):
        vs = VectorStore(dimension=DIM)
        _add_vec(vs, "entity", "ent_1")
        _add_vec(vs, "facet_point", "fp_1")

        result = discover_anchors(_make_pq(), vs, FakeEmbedder())
        assert "ent_1" in result.node_distances
        assert "fp_1" in result.node_distances

    def test_returns_edge_distances(self):
        vs = VectorStore(dimension=DIM)
        _add_vec(vs, "edge_relation", "edge_1")

        result = discover_anchors(_make_pq(), vs, FakeEmbedder())
        assert "edge_1" in result.edge_distances

    def test_edge_belongs_to_skipped(self):
        vs = VectorStore(dimension=DIM)
        _add_vec(vs, "edge_belongs_to", "bt_1")

        result = discover_anchors(_make_pq(), vs, FakeEmbedder())
        assert "bt_1" not in result.node_distances
        assert "bt_1" not in result.edge_distances


class TestEmptyGraph:
    def test_empty_store_returns_empty(self):
        vs = VectorStore(dimension=DIM)
        result = discover_anchors(_make_pq(), vs, FakeEmbedder())
        assert result.node_distances == {}
        assert result.edge_distances == {}


class TestMinDistance:
    def test_same_node_in_two_indexes_takes_min(self):
        vs = VectorStore(dimension=DIM)
        vec_close = np.ones(DIM, dtype=np.float32) / np.sqrt(DIM)
        vec_far = np.zeros(DIM, dtype=np.float32)
        vec_far[0] = 1.0

        vs.add("entity", ["node_1"], vec_close.reshape(1, -1))
        vs.add("facet_point", ["node_1"], vec_far.reshape(1, -1))

        result = discover_anchors(_make_pq(), vs, FakeEmbedder())
        dist = result.node_distances["node_1"]
        assert dist < 0.01  # close vector → near-zero distance


class TestHitsByIndex:
    def test_hits_by_index_populated(self):
        vs = VectorStore(dimension=DIM)
        _add_vec(vs, "entity", "ent_1")
        _add_vec(vs, "episode", "ep_1")

        result = discover_anchors(_make_pq(), vs, FakeEmbedder())
        assert "entity" in result.hits_by_index
        assert "episode" in result.hits_by_index
        assert len(result.hits_by_index["entity"]) == 1
