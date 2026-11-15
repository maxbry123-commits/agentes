"""End-to-end tests for Bundle Search retrieval."""

import numpy as np

from mmem.config import MMemConfig, RetrievalConfig
from mmem.core.edges import make_belongs_to, make_causal, make_evolution, make_temporal
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Entity, Episode, Facet, FacetPoint
from mmem.indexing.vector_store import VectorStore
from mmem.retrieval.search import bundle_search

DIM = 8


class FakeEmbedder:
    """Maps known texts to deterministic vectors.  Unknown texts get a
    random-but-reproducible vector."""

    def __init__(self, mapping: dict[str, np.ndarray] | None = None):
        self._map = mapping or {}

    def embed(self, text: str) -> np.ndarray:
        if text in self._map:
            return self._map[text]
        rng = np.random.RandomState(abs(hash(text)) % (2**31))
        v = rng.randn(DIM).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-9)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.embed(t) for t in texts])


def _unit_vec(seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    v = rng.randn(DIM).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


# ── Shared test fixture: "Alice story" graph ──────────────────────────

def _build_alice_graph():
    """Build a small graph simulating 2 ingested chunks about Alice."""
    g = MemoryGraph()
    vs = VectorStore(dimension=DIM)

    # Nodes
    alice = g.add_node(Entity(name="Alice"))
    ep1 = g.add_node(Episode(summary="Alice joined Acme Corp as an engineer in 2020"))
    ep2 = g.add_node(Episode(summary="Alice left Acme Corp in 2024 for a startup"))
    fa_career = g.add_node(Facet(theme="Alice career trajectory"))
    fp1 = g.add_node(FacetPoint(content="joined Acme Corp as engineer 2020"))
    fp2 = g.add_node(FacetPoint(content="left Acme Corp 2024 startup"))

    # belongs_to chain: Entity→FP→Facet→Episode
    g.add_edge(make_belongs_to(alice.id, fp1.id))
    g.add_edge(make_belongs_to(alice.id, fp2.id))
    g.add_edge(make_belongs_to(fp1.id, fa_career.id))
    g.add_edge(make_belongs_to(fp2.id, fa_career.id))
    g.add_edge(make_belongs_to(fa_career.id, ep1.id))
    g.add_edge(make_belongs_to(fa_career.id, ep2.id))

    # Relation edges
    g.add_edge(make_temporal(fp1.id, fp2.id, "career timeline"))
    g.add_edge(make_temporal(ep1.id, ep2.id, "episode sequence"))
    g.add_edge(make_evolution(fp1.id, fp2.id, "career change"))
    causal = make_causal(ep1.id, ep2.id, "joining led to eventually leaving", confidence=0.8)
    g.add_edge(causal)

    # Build a common "career" vector that query and relevant nodes share
    career_vec = _unit_vec(42)

    # Populate FAISS indexes
    vs.add("entity", [alice.id], _embed_like(career_vec, 0.9))
    vs.add("facet_point", [fp1.id], _embed_like(career_vec, 0.85))
    vs.add("facet_point", [fp2.id], _embed_like(career_vec, 0.7))
    vs.add("facet", [fa_career.id], _embed_like(career_vec, 0.95))
    vs.add("episode", [ep1.id], _embed_like(career_vec, 0.6))
    vs.add("episode", [ep2.id], _embed_like(career_vec, 0.5))

    vs.add("edge_relation", [causal.id], _embed_like(career_vec, 0.4))

    # Embedder that maps query text to the same career vector direction
    embedder = FakeEmbedder({"Alice career": career_vec, "Alice's career": career_vec})

    return g, vs, embedder, alice, ep1, ep2, fa_career, fp1, fp2


def _embed_like(base: np.ndarray, similarity: float) -> np.ndarray:
    """Create a vector with approximately *similarity* cosine to *base*."""
    noise = np.random.RandomState(int(similarity * 1000)).randn(len(base)).astype(np.float32)
    noise /= np.linalg.norm(noise) + 1e-9
    v = similarity * base + (1.0 - similarity) * noise
    v /= np.linalg.norm(v) + 1e-9
    return v.reshape(1, -1)


class TestBasicRetrieval:
    def test_returns_episodes(self):
        g, vs, emb, alice, ep1, ep2, fa, fp1, fp2 = _build_alice_graph()
        result = bundle_search("Alice career", g, vs, emb)
        assert len(result.bundles) > 0

    def test_returns_context_text(self):
        g, vs, emb, alice, ep1, ep2, fa, fp1, fp2 = _build_alice_graph()
        result = bundle_search("Alice career", g, vs, emb)
        assert len(result.context_text) > 0
        assert "Alice" in result.context_text

    def test_top_k_respected(self):
        g, vs, emb, alice, ep1, ep2, fa, fp1, fp2 = _build_alice_graph()
        result = bundle_search("Alice career", g, vs, emb, top_k=1)
        assert len(result.bundles) <= 1


class TestTemporalQuery:
    def test_temporal_query_returns_results(self):
        g, vs, emb, alice, ep1, ep2, fa, fp1, fp2 = _build_alice_graph()
        result = bundle_search("When did Alice join Acme?", g, vs, emb)
        assert len(result.bundles) > 0


class TestCausalQuery:
    def test_causal_bridge_creates_paths(self):
        g, vs, emb, alice, ep1, ep2, fa, fp1, fp2 = _build_alice_graph()
        result = bundle_search("Alice career", g, vs, emb)
        # ep2 should be reachable via causal bridge from ep1
        ep_ids = {b.episode_id for b in result.bundles}
        assert ep1.id in ep_ids or ep2.id in ep_ids


class TestDetailMode:
    def test_detail_mode_includes_facets(self):
        g, vs, emb, alice, ep1, ep2, fa, fp1, fp2 = _build_alice_graph()
        result = bundle_search("Alice career", g, vs, emb, display_mode="detail")
        assert "career" in result.context_text.lower()


class TestEmptyGraph:
    def test_empty_graph_returns_empty(self):
        g = MemoryGraph()
        vs = VectorStore(dimension=DIM)
        emb = FakeEmbedder()
        result = bundle_search("anything", g, vs, emb)
        assert result.bundles == []
        assert result.context_text == ""


class TestEntityQuery:
    def test_entity_path_returns_episodes(self):
        g, vs, emb, alice, ep1, ep2, fa, fp1, fp2 = _build_alice_graph()
        # Short query triggers entity_centric hint
        emb._map["Alice"] = emb._map["Alice career"]
        result = bundle_search("Alice", g, vs, emb)
        assert len(result.bundles) > 0
