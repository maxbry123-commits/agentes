"""
Multi-round ingestion integration test.

Ingests 5 sequential chunks through the full IngestionPipeline with
overlapping entities and similar facet themes, then verifies cross-chunk
behaviours: entity dedup, facet merge, temporal chain, evolution chain,
checkpoint round-trip, consolidation, and idempotency.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from mmem.config import MMemConfig, WriteConfig
from mmem.core.edges import EdgeType
from mmem.core.nodes import Entity, Episode, Facet, FacetPoint, NodeType
from mmem.indexing.vector_store import VectorStore
from mmem.ingestion.extractor import (
    CausalPair,
    EntityInfo,
    ExtractionResult,
    FacetInfo,
    FacetPointInfo,
    TemporalInfo,
)
from mmem.ingestion.pipeline import IngestionPipeline

DIM = 8

# ── Shared embedding vectors ─────────────────────────────────────────

_CAREER_VEC: np.ndarray | None = None
_OTHER_VECS: dict[str, np.ndarray] = {}


def _stable_vec(seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    v = rng.randn(DIM).astype(np.float32)
    return v / np.linalg.norm(v)


def _get_career_vec() -> np.ndarray:
    global _CAREER_VEC
    if _CAREER_VEC is None:
        _CAREER_VEC = _stable_vec(42)
    return _CAREER_VEC


def _get_other_vec(key: str) -> np.ndarray:
    if key not in _OTHER_VECS:
        _OTHER_VECS[key] = _stable_vec(hash(key) % (2**31))
    return _OTHER_VECS[key]


# ── Fake collaborators ───────────────────────────────────────────────

CAREER_THEMES = {"career", "career development", "career path"}


class FakeEmbedder:
    """Returns identical vectors for career-related themes so facet merge fires."""

    @property
    def dimension(self) -> int:
        return DIM

    def embed(self, text: str) -> np.ndarray:
        if text.strip().lower() in CAREER_THEMES:
            return _get_career_vec().copy()
        return _get_other_vec(text).copy()

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.embed(t) for t in texts])


class FakeExtractor:
    def __init__(self, results: list[ExtractionResult]) -> None:
        self._results = list(results)
        self._idx = 0
        self.causal_pairs: list[CausalPair] = []

    def extract(self, chunk: str) -> ExtractionResult:
        r = self._results[self._idx % len(self._results)]
        self._idx += 1
        return r

    def extract_causal(self, episodes) -> list[CausalPair]:
        return list(self.causal_pairs)


# ── 5-chunk extraction results ───────────────────────────────────────

CHUNK_RESULTS = [
    # C1: Alice joins Acme
    ExtractionResult(
        episode_summary="Alice joined Acme Corp as a junior engineer.",
        entities=[
            EntityInfo(name="Alice", entity_type="person"),
            EntityInfo(name="Acme Corp", entity_type="organization"),
        ],
        facet_points=[
            FacetPointInfo(
                content="Alice joined Acme Corp in 2020",
                related_entity_name="Alice",
                timestamp_text="2020",
            ),
        ],
        facets=[FacetInfo(theme="Career", facet_point_indices=[0])],
        temporal_info=[
            TemporalInfo(subject="Alice", time_expression="in 2020", normalized_time="2020"),
        ],
    ),
    # C2: Alice gets promoted
    ExtractionResult(
        episode_summary="Alice was promoted to senior engineer at Acme.",
        entities=[EntityInfo(name="Alice", entity_type="person")],
        facet_points=[
            FacetPointInfo(
                content="Alice got promoted in 2021",
                related_entity_name="Alice",
                timestamp_text="2021",
            ),
        ],
        facets=[FacetInfo(theme="Career Development", facet_point_indices=[0])],
        temporal_info=[
            TemporalInfo(subject="Alice", time_expression="in 2021", normalized_time="2021"),
        ],
    ),
    # C3: Alice meets Bob
    ExtractionResult(
        episode_summary="Alice met Bob at a tech conference.",
        entities=[
            EntityInfo(name="Alice", entity_type="person"),
            EntityInfo(name="Bob", entity_type="person"),
        ],
        facet_points=[
            FacetPointInfo(
                content="Alice met Bob in 2022",
                related_entity_name="Alice",
                timestamp_text="2022",
            ),
        ],
        facets=[FacetInfo(theme="Social", facet_point_indices=[0])],
        temporal_info=[
            TemporalInfo(subject="Alice", time_expression="in 2022", normalized_time="2022"),
        ],
    ),
    # C4: Alice leaves Acme
    ExtractionResult(
        episode_summary="Alice resigned from Acme Corp to pursue new opportunities.",
        entities=[EntityInfo(name="Alice", entity_type="person")],
        facet_points=[
            FacetPointInfo(
                content="Alice left Acme in 2023",
                related_entity_name="Alice",
                timestamp_text="2023",
            ),
        ],
        facets=[FacetInfo(theme="Career Path", facet_point_indices=[0])],
        temporal_info=[
            TemporalInfo(subject="Alice", time_expression="in 2023", normalized_time="2023"),
        ],
    ),
    # C5: Alice and Bob start a company
    ExtractionResult(
        episode_summary="Alice and Bob co-founded a startup in 2024.",
        entities=[
            EntityInfo(name="Alice", entity_type="person"),
            EntityInfo(name="Bob", entity_type="person"),
        ],
        facet_points=[
            FacetPointInfo(
                content="Alice and Bob started a company in 2024",
                related_entity_name="Alice",
                timestamp_text="2024",
            ),
        ],
        facets=[FacetInfo(theme="Entrepreneurship", facet_point_indices=[0])],
        temporal_info=[
            TemporalInfo(subject="Alice", time_expression="in 2024", normalized_time="2024"),
        ],
    ),
]

CHUNKS = [
    "Alice joined Acme Corp as a junior engineer in 2020.",
    "Alice was promoted to senior engineer at Acme in 2021.",
    "Alice met Bob at a tech conference in 2022.",
    "Alice resigned from Acme Corp in 2023.",
    "Alice and Bob co-founded a startup in 2024.",
]


# ── Helpers ───────────────────────────────────────────────────────────


def _build_pipeline(
    config: MMemConfig | None = None,
    results: list[ExtractionResult] | None = None,
) -> IngestionPipeline:
    cfg = config or MMemConfig(
        write=WriteConfig(causal_consolidation_interval=5),
    )
    embedder = FakeEmbedder()
    pipeline = IngestionPipeline(
        config=cfg,
        embedder=embedder,
        vector_store=VectorStore(dimension=DIM),
    )
    pipeline._extractor = FakeExtractor(results or CHUNK_RESULTS)  # type: ignore[assignment]
    return pipeline


def _ingest_all(pipeline: IngestionPipeline) -> None:
    for chunk in CHUNKS:
        pipeline.ingest(chunk)


# ═══════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════


class TestEntityDedupAcrossChunks:
    def test_alice_appears_once(self):
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        entities = pipeline.graph.get_nodes_by_type(NodeType.ENTITY)
        alice_entities = [e for e in entities if isinstance(e, Entity) and e.name == "Alice"]
        assert len(alice_entities) == 1

    def test_total_entity_count(self):
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        entities = pipeline.graph.get_nodes_by_type(NodeType.ENTITY)
        names = {e.name for e in entities if isinstance(e, Entity)}
        assert names == {"Alice", "Acme Corp", "Bob"}


class TestFacetMergeAcrossChunks:
    def test_career_themes_merge_into_one(self):
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        facets = pipeline.graph.get_nodes_by_type(NodeType.FACET)
        facet_themes = [f.theme for f in facets if isinstance(f, Facet)]
        career_facets = [t for t in facet_themes if t.lower() in CAREER_THEMES]
        assert len(career_facets) == 1

    def test_total_facet_count(self):
        """Career(merged) + Social + Entrepreneurship = 3"""
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        facets = pipeline.graph.get_nodes_by_type(NodeType.FACET)
        assert len(facets) == 3

    def test_merged_facet_connects_to_multiple_episodes(self):
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        facets = pipeline.graph.get_nodes_by_type(NodeType.FACET)
        career_facet = None
        for f in facets:
            if isinstance(f, Facet) and f.theme.lower() in CAREER_THEMES:
                career_facet = f
                break
        assert career_facet is not None

        parent_eps = pipeline.graph.get_parent_episodes(career_facet.id)
        assert len(parent_eps) >= 2


class TestEpisodeTemporalChain:
    def test_five_episodes_four_temporal_edges(self):
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        episodes = pipeline.graph.get_nodes_by_type(NodeType.EPISODE)
        assert len(episodes) == 5

        temp_edges = pipeline.graph.get_edges_by_type(EdgeType.TEMPORAL)
        ep_temporal = [
            e for e in temp_edges if "episode sequence" in e.description
        ]
        assert len(ep_temporal) == 4

    def test_temporal_chain_is_continuous(self):
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        episodes = sorted(
            pipeline.graph.get_nodes_by_type(NodeType.EPISODE),
            key=lambda ep: ep.created_at,
        )
        ep_ids = [ep.id for ep in episodes]

        temp_edges = pipeline.graph.get_edges_by_type(EdgeType.TEMPORAL)
        ep_temporal_pairs = {
            (e.source_id, e.target_id)
            for e in temp_edges
            if "episode sequence" in e.description
        }

        for i in range(len(ep_ids) - 1):
            assert (ep_ids[i], ep_ids[i + 1]) in ep_temporal_pairs


class TestEvolutionChainForEntity:
    def test_alice_evolution_chain(self):
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        evo_edges = pipeline.graph.get_edges_by_type(EdgeType.EVOLUTION)
        assert len(evo_edges) == 4  # fp1→fp2→fp3→fp4→fp5

    def test_evolution_edges_connect_alice_fps_in_order(self):
        pipeline = _build_pipeline()
        _ingest_all(pipeline)

        fps = pipeline.graph.get_nodes_by_type(NodeType.FACET_POINT)
        alice_entity = pipeline.graph.get_entity_by_name("Alice")
        assert alice_entity is not None

        alice_fps = [
            fp for fp in fps
            if isinstance(fp, FacetPoint) and fp.related_entity_id == alice_entity.id
        ]
        alice_fps.sort(key=lambda fp: fp.timestamp or fp.created_at)
        assert len(alice_fps) == 5

        evo_edges = pipeline.graph.get_edges_by_type(EdgeType.EVOLUTION)
        evo_pairs = {(e.source_id, e.target_id) for e in evo_edges}

        for i in range(len(alice_fps) - 1):
            assert (alice_fps[i].id, alice_fps[i + 1].id) in evo_pairs


class TestCheckpointRoundTrip:
    def test_checkpoint_preserves_full_state(self, tmp_path: Path):
        pipeline1 = _build_pipeline()
        for chunk in CHUNKS[:3]:
            pipeline1.ingest(chunk)

        ckpt = tmp_path / "ckpt"
        pipeline1.save_checkpoint(ckpt)

        pipeline2 = IngestionPipeline.load_checkpoint(
            ckpt, embedder=FakeEmbedder(),
        )
        pipeline2._extractor = FakeExtractor(CHUNK_RESULTS[3:])  # type: ignore[assignment]

        for chunk in CHUNKS[3:]:
            pipeline2.ingest(chunk)

        ref = _build_pipeline()
        _ingest_all(ref)

        assert pipeline2.graph.num_nodes == ref.graph.num_nodes
        assert pipeline2.graph.num_edges == ref.graph.num_edges
        assert pipeline2.stats()["episode_count"] == 5
        assert pipeline2.stats()["ingested_chunks"] == 5

    def test_checkpoint_preserves_facet_merge(self, tmp_path: Path):
        pipeline1 = _build_pipeline()
        pipeline1.ingest(CHUNKS[0])  # Career
        pipeline1.save_checkpoint(tmp_path / "ckpt")

        pipeline2 = IngestionPipeline.load_checkpoint(
            tmp_path / "ckpt", embedder=FakeEmbedder(),
        )
        pipeline2._extractor = FakeExtractor(CHUNK_RESULTS[1:])  # type: ignore[assignment]
        pipeline2.ingest(CHUNKS[1])  # Career Development

        facets = pipeline2.graph.get_nodes_by_type(NodeType.FACET)
        career_facets = [
            f for f in facets
            if isinstance(f, Facet) and f.theme.lower() in CAREER_THEMES
        ]
        assert len(career_facets) == 1


class TestConsolidationFires:
    def test_causal_edges_appear_after_interval(self):
        pipeline = _build_pipeline()

        for chunk in CHUNKS[:4]:
            pipeline.ingest(chunk)
        assert len(pipeline.graph.get_edges_by_type(EdgeType.CAUSAL)) == 0

        eps = sorted(
            pipeline.graph.get_nodes_by_type(NodeType.EPISODE),
            key=lambda ep: ep.created_at,
        )
        pipeline._extractor.causal_pairs = [  # type: ignore[attr-defined]
            CausalPair(
                cause_id=eps[0].id,
                effect_id=eps[1].id,
                description="Joining Acme led to promotion",
                confidence=0.9,
            ),
        ]

        pipeline.ingest(CHUNKS[4])

        causal = pipeline.graph.get_edges_by_type(EdgeType.CAUSAL)
        assert len(causal) == 1
        assert causal[0].description == "Joining Acme led to promotion"


class TestIdempotencyAcrossCheckpoint:
    def test_re_ingest_after_restore_returns_none(self, tmp_path: Path):
        pipeline1 = _build_pipeline()
        _ingest_all(pipeline1)
        pipeline1.save_checkpoint(tmp_path / "ckpt")

        pipeline2 = IngestionPipeline.load_checkpoint(
            tmp_path / "ckpt", embedder=FakeEmbedder(),
        )
        pipeline2._extractor = FakeExtractor(CHUNK_RESULTS)  # type: ignore[assignment]

        for chunk in CHUNKS:
            assert pipeline2.ingest(chunk) is None

        assert pipeline2.stats()["ingested_chunks"] == 5
