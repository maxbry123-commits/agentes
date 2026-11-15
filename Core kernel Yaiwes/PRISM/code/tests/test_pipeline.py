"""Tests for IngestionPipeline and MemoryGraph persistence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from mmem.config import MMemConfig, WriteConfig
from mmem.core.edges import EdgeType, make_belongs_to, make_temporal
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Entity, Episode, Facet, FacetPoint, NodeType
from mmem.indexing.vector_store import VectorStore
from mmem.ingestion.extractor import (
    EntityInfo,
    ExtractionResult,
    FacetInfo,
    FacetPointInfo,
    TemporalInfo,
)
from mmem.ingestion.pipeline import IngestionPipeline

DIM = 8


# ── Fake collaborators ───────────────────────────────────────────────


class FakeEmbedder:
    """Deterministic embedder that maps text to a reproducible unit vector."""

    def __init__(self) -> None:
        self.call_count = 0

    @property
    def dimension(self) -> int:
        return DIM

    def embed(self, text: str) -> np.ndarray:
        self.call_count += 1
        rng = np.random.RandomState(hash(text) % (2**31))
        vec = rng.randn(DIM).astype(np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        self.call_count += 1
        return np.stack([self.embed(t) for t in texts])


class FakeExtractor:
    """Returns canned ExtractionResults, one per call."""

    def __init__(self, results: list[ExtractionResult]) -> None:
        self._results = list(results)
        self._idx = 0
        self.causal_pairs: list = []

    def extract(self, chunk: str) -> ExtractionResult:
        r = self._results[self._idx % len(self._results)]
        self._idx += 1
        return r

    def extract_causal(self, episodes) -> list:
        return list(self.causal_pairs)


def _make_result(
    summary: str = "Alice joined Acme Corp.",
    entities: list[EntityInfo] | None = None,
    facet_points: list[FacetPointInfo] | None = None,
    facets: list[FacetInfo] | None = None,
) -> ExtractionResult:
    return ExtractionResult(
        episode_summary=summary,
        entities=[EntityInfo(name="Alice", entity_type="person")] if entities is None else entities,
        facet_points=[
            FacetPointInfo(content="Alice joined Acme Corp.", related_entity_name="Alice"),
        ] if facet_points is None else facet_points,
        facets=[
            FacetInfo(theme="Career", facet_point_indices=[0]),
        ] if facets is None else facets,
    )


def _build_pipeline(
    results: list[ExtractionResult] | None = None,
    config: MMemConfig | None = None,
) -> tuple[IngestionPipeline, FakeEmbedder]:
    """Create a pipeline with fake extractor and embedder."""
    cfg = config or MMemConfig()
    embedder = FakeEmbedder()
    graph = MemoryGraph()
    vs = VectorStore(dimension=DIM)

    pipeline = IngestionPipeline(
        config=cfg,
        graph=graph,
        vector_store=vs,
        embedder=embedder,
    )

    fake_extractor = FakeExtractor(results or [_make_result()])
    pipeline._extractor = fake_extractor  # type: ignore[assignment]

    return pipeline, embedder


# ═══════════════════════════════════════════════════════════════════════
# MemoryGraph persistence
# ═══════════════════════════════════════════════════════════════════════


class TestMemoryGraphPersistence:
    def test_to_dict_and_from_dict_round_trip(self):
        g = MemoryGraph()
        e = Entity(name="Alice", entity_type="person")
        ep = Episode(summary="First meeting")
        fp = FacetPoint(content="Alice arrived", related_entity_id=e.id)
        f = Facet(theme="Social")

        g.add_node(e)
        g.add_node(ep)
        g.add_node(fp)
        g.add_node(f)
        g.add_edge(make_belongs_to(e.id, fp.id))
        g.add_edge(make_temporal(fp.id, ep.id))

        data = g.to_dict()
        g2 = MemoryGraph.from_dict(data)

        assert g2.num_nodes == g.num_nodes
        assert g2.num_edges == g.num_edges
        assert g2.get_entity_by_name("Alice") is not None
        assert g2.get_node(ep.id) is not None

    def test_save_and_load_file(self, tmp_path: Path):
        g = MemoryGraph()
        e = Entity(name="Bob")
        ep = Episode(summary="Bob's story")
        g.add_node(e)
        g.add_node(ep)
        g.add_edge(make_belongs_to(e.id, ep.id))

        fpath = tmp_path / "graph.json"
        g.save(fpath)
        assert fpath.exists()

        g2 = MemoryGraph.load(fpath)
        assert g2.num_nodes == 2
        assert g2.num_edges == 1
        assert g2.get_entity_by_name("Bob") is not None

    def test_round_trip_preserves_node_fields(self):
        g = MemoryGraph()
        fp = FacetPoint(
            content="test content",
            related_entity_id="ent123",
            timestamp_text="2024-01-15",
        )
        g.add_node(fp)

        g2 = MemoryGraph.from_dict(g.to_dict())
        fp2 = g2.get_node(fp.id)
        assert isinstance(fp2, FacetPoint)
        assert fp2.content == "test content"
        assert fp2.related_entity_id == "ent123"
        assert fp2.timestamp_text == "2024-01-15"

    def test_round_trip_preserves_edge_fields(self):
        g = MemoryGraph()
        e1 = Entity(name="A")
        e2 = Entity(name="B")
        g.add_node(e1)
        g.add_node(e2)
        from mmem.core.edges import make_causal
        edge = make_causal(e1.id, e2.id, "A caused B", confidence=0.85)
        g.add_edge(edge)

        g2 = MemoryGraph.from_dict(g.to_dict())
        edges = g2.get_edges_by_type(EdgeType.CAUSAL)
        assert len(edges) == 1
        assert edges[0].description == "A caused B"
        assert edges[0].confidence == pytest.approx(0.85)

    def test_entity_name_index_restored(self):
        g = MemoryGraph()
        g.add_node(Entity(name="Charlie"))
        g.add_node(Entity(name="Diana"))

        g2 = MemoryGraph.from_dict(g.to_dict())
        assert g2.get_entity_by_name("charlie") is not None
        assert g2.get_entity_by_name("diana") is not None
        assert g2.get_entity_by_name("unknown") is None

    def test_from_dict_skips_orphaned_edges(self):
        data = {
            "nodes": [
                {"__node_type__": "entity", "id": "a", "name": "A", "entity_type": "person"},
            ],
            "edges": [
                {
                    "id": "e1",
                    "source_id": "a",
                    "target_id": "nonexistent",
                    "edge_type": "belongs_to",
                },
            ],
        }
        g = MemoryGraph.from_dict(data)
        assert g.num_nodes == 1
        assert g.num_edges == 0


# ═══════════════════════════════════════════════════════════════════════
# Basic ingestion
# ═══════════════════════════════════════════════════════════════════════


class TestBasicIngest:
    def test_ingest_returns_build_result(self):
        pipeline, _ = _build_pipeline()
        br = pipeline.ingest("Alice joined Acme Corp in 2024.")
        assert br is not None
        assert br.episode_id

    def test_ingest_creates_nodes(self):
        pipeline, _ = _build_pipeline()
        pipeline.ingest("chunk1")

        g = pipeline.graph
        assert len(g.get_nodes_by_type(NodeType.EPISODE)) == 1
        assert len(g.get_nodes_by_type(NodeType.ENTITY)) >= 1

    def test_ingest_populates_faiss(self):
        pipeline, _ = _build_pipeline()
        pipeline.ingest("chunk1")

        vs = pipeline.vector_store
        assert vs.count("episode") >= 1
        assert vs.count("facet_point") >= 1


# ═══════════════════════════════════════════════════════════════════════
# Idempotency
# ═══════════════════════════════════════════════════════════════════════


class TestIdempotency:
    def test_same_chunk_ingested_twice_returns_none(self):
        pipeline, _ = _build_pipeline()
        br1 = pipeline.ingest("same chunk")
        br2 = pipeline.ingest("same chunk")
        assert br1 is not None
        assert br2 is None

    def test_same_chunk_no_duplicate_nodes(self):
        pipeline, _ = _build_pipeline()
        pipeline.ingest("same chunk")
        pipeline.ingest("same chunk")
        assert len(pipeline.graph.get_nodes_by_type(NodeType.EPISODE)) == 1

    def test_different_chunks_both_ingested(self):
        r1 = _make_result(summary="Ep1")
        r2 = _make_result(summary="Ep2")
        pipeline, _ = _build_pipeline(results=[r1, r2])

        pipeline.ingest("chunk A")
        pipeline.ingest("chunk B")
        assert len(pipeline.graph.get_nodes_by_type(NodeType.EPISODE)) == 2


# ═══════════════════════════════════════════════════════════════════════
# Vectorisation
# ═══════════════════════════════════════════════════════════════════════


class TestVectorisation:
    def test_belongs_to_edges_not_indexed(self):
        pipeline, _ = _build_pipeline()
        pipeline.ingest("chunk1")

        vs = pipeline.vector_store
        assert vs.count("edge_belongs_to") == 0

    def test_temporal_edges_indexed_as_edge_relation(self):
        r1 = _make_result(summary="Ep1", entities=[], facet_points=[], facets=[])
        r2 = _make_result(summary="Ep2", entities=[], facet_points=[], facets=[])
        pipeline, _ = _build_pipeline(results=[r1, r2])

        pipeline.ingest("chunk1")
        pipeline.ingest("chunk2")

        assert pipeline.vector_store.count("edge_relation") >= 1

    def test_already_indexed_entities_not_double_embedded(self, ):
        pipeline, embedder = _build_pipeline()
        embedder.call_count = 0
        pipeline.ingest("chunk1")

        ep_count = pipeline.vector_store.count("episode")
        fp_count = pipeline.vector_store.count("facet_point")
        ent_count = pipeline.vector_store.count("entity")
        facet_count = pipeline.vector_store.count("facet")

        assert ep_count == 1
        assert ent_count >= 1
        assert fp_count >= 1
        assert facet_count >= 1

    def test_involves_entity_edges_indexed_as_edge_relation(self):
        pipeline, _ = _build_pipeline()
        pipeline.ingest("chunk1")

        from mmem.core.edges import EdgeType
        involves = pipeline.graph.get_edges_by_type(EdgeType.INVOLVES_ENTITY)
        assert len(involves) >= 1

        edge_relation_count = pipeline.vector_store.count("edge_relation")
        assert edge_relation_count >= len(involves)


# ═══════════════════════════════════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════════════════════════════════


class TestStats:
    def test_stats_structure(self):
        pipeline, _ = _build_pipeline()
        pipeline.ingest("chunk1")
        s = pipeline.stats()

        assert "graph" in s
        assert "vector_store" in s
        assert "episode_count" in s
        assert "ingested_chunks" in s
        assert s["episode_count"] == 1
        assert s["ingested_chunks"] == 1

    def test_stats_increments(self):
        r1 = _make_result(summary="Ep1")
        r2 = _make_result(summary="Ep2")
        pipeline, _ = _build_pipeline(results=[r1, r2])

        pipeline.ingest("c1")
        pipeline.ingest("c2")
        s = pipeline.stats()
        assert s["episode_count"] == 2
        assert s["ingested_chunks"] == 2


# ═══════════════════════════════════════════════════════════════════════
# Checkpoint save / load
# ═══════════════════════════════════════════════════════════════════════


class TestCheckpoint:
    def test_save_creates_expected_files(self, tmp_path: Path):
        pipeline, _ = _build_pipeline()
        pipeline.ingest("chunk1")
        pipeline.save_checkpoint(tmp_path / "ckpt")

        ckpt = tmp_path / "ckpt"
        assert (ckpt / "graph.json").exists()
        assert (ckpt / "faiss" / "metadata.json").exists()
        assert (ckpt / "pipeline_state.json").exists()
        assert (ckpt / "chunks.json").exists()

    def test_save_load_round_trip(self, tmp_path: Path):
        r1 = _make_result(summary="Ep1")
        r2 = _make_result(summary="Ep2")
        pipeline, _ = _build_pipeline(results=[r1, r2])
        pipeline.ingest("chunk A")
        pipeline.ingest("chunk B")

        ckpt = tmp_path / "ckpt"
        pipeline.save_checkpoint(ckpt)

        embedder2 = FakeEmbedder()
        pipeline2 = IngestionPipeline.load_checkpoint(
            ckpt, embedder=embedder2,
        )

        assert pipeline2.stats()["episode_count"] == 2
        assert pipeline2.stats()["ingested_chunks"] == 2
        assert pipeline2.graph.num_nodes == pipeline.graph.num_nodes
        assert pipeline2.graph.num_edges == pipeline.graph.num_edges

    def test_load_preserves_idempotency(self, tmp_path: Path):
        pipeline, _ = _build_pipeline()
        pipeline.ingest("chunk1")
        pipeline.save_checkpoint(tmp_path / "ckpt")

        r2 = _make_result(summary="Ep2")
        pipeline2, _ = _build_pipeline(results=[r2])
        pipeline2 = IngestionPipeline.load_checkpoint(
            tmp_path / "ckpt", embedder=FakeEmbedder(),
        )
        pipeline2._extractor = FakeExtractor([r2])  # type: ignore[assignment]

        br = pipeline2.ingest("chunk1")
        assert br is None

        br2 = pipeline2.ingest("chunk2")
        assert br2 is not None

    def test_checkpoint_state_has_no_last_episode_id(self, tmp_path: Path):
        """last_episode_id is no longer persisted (sorted insertion replaced it)."""
        r1 = _make_result(summary="Ep1", entities=[], facet_points=[], facets=[])
        pipeline, _ = _build_pipeline(results=[r1])
        pipeline.ingest("c1")
        ckpt = tmp_path / "ckpt"
        pipeline.save_checkpoint(ckpt)

        state = json.loads((ckpt / "pipeline_state.json").read_text(encoding="utf-8"))
        assert "last_episode_id" not in state

    def test_load_preserves_episode_temporal_chain(self, tmp_path: Path):
        r1 = _make_result(summary="Ep1", entities=[], facet_points=[], facets=[])
        r2 = _make_result(summary="Ep2", entities=[], facet_points=[], facets=[])
        r3 = _make_result(summary="Ep3", entities=[], facet_points=[], facets=[])

        pipeline, _ = _build_pipeline(results=[r1, r2])
        pipeline.ingest("c1")
        pipeline.save_checkpoint(tmp_path / "ckpt")

        pipeline2 = IngestionPipeline.load_checkpoint(
            tmp_path / "ckpt", embedder=FakeEmbedder(),
        )
        pipeline2._extractor = FakeExtractor([r2, r3])  # type: ignore[assignment]
        pipeline2.ingest("c2")
        pipeline2.ingest("c3")

        temp_edges = pipeline2.graph.get_edges_by_type(EdgeType.TEMPORAL)
        assert len(temp_edges) == 2


# ═══════════════════════════════════════════════════════════════════════
# Consolidation
# ═══════════════════════════════════════════════════════════════════════


class TestConsolidation:
    def test_consolidation_creates_causal_edges_at_interval(self):
        from mmem.ingestion.extractor import CausalPair

        cfg = MMemConfig(write=WriteConfig(causal_consolidation_interval=2))
        pipeline, _ = _build_pipeline(
            results=[
                _make_result(summary="Ep1", entities=[], facet_points=[], facets=[]),
                _make_result(summary="Ep2", entities=[], facet_points=[], facets=[]),
            ],
            config=cfg,
        )

        pipeline.ingest("c1")
        pipeline.ingest("c2")

        ep_ids = [
            ep.id for ep in pipeline.graph.get_nodes_by_type(NodeType.EPISODE)
        ]
        assert len(ep_ids) == 2

        pipeline._extractor.causal_pairs = [  # type: ignore[attr-defined]
            CausalPair(
                cause_id=ep_ids[0],
                effect_id=ep_ids[1],
                description="Ep1 caused Ep2",
                confidence=0.9,
            ),
        ]

        r3 = _make_result(summary="Ep3", entities=[], facet_points=[], facets=[])
        r4 = _make_result(summary="Ep4", entities=[], facet_points=[], facets=[])
        pipeline._extractor._results = [r3, r4]  # type: ignore[attr-defined]
        pipeline._extractor._idx = 0  # type: ignore[attr-defined]

        pipeline.ingest("c3")
        pipeline.ingest("c4")

        causal = pipeline.graph.get_edges_by_type(EdgeType.CAUSAL)
        assert len(causal) >= 1

    def test_consolidation_disabled(self):
        cfg = MMemConfig(
            write=WriteConfig(
                enable_causal_consolidation=False,
                causal_consolidation_interval=1,
            ),
        )
        pipeline, _ = _build_pipeline(
            results=[_make_result(summary="Ep1", entities=[], facet_points=[], facets=[])],
            config=cfg,
        )
        pipeline.ingest("c1")

        causal = pipeline.graph.get_edges_by_type(EdgeType.CAUSAL)
        assert len(causal) == 0
