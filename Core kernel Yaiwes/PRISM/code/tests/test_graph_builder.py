"""Tests for GraphBuilder — the core ingestion graph construction logic."""

from __future__ import annotations

import numpy as np
import pytest

from mmem.config import MMemConfig
from mmem.core.edges import EdgeType
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
from mmem.ingestion.graph_builder import BuildResult, GraphBuilder, _try_parse_timestamp

DIM = 8


class FakeEmbedder:
    """Deterministic embedder for testing.

    Accepts a dict mapping text → vector.  Unknown texts get a random
    (but reproducible) vector derived from the text hash.
    """

    def __init__(self, mapping: dict[str, np.ndarray] | None = None):
        self._mapping = mapping or {}

    @property
    def dimension(self) -> int:
        return DIM

    def embed(self, text: str) -> np.ndarray:
        if text in self._mapping:
            return self._mapping[text]
        rng = np.random.RandomState(hash(text) % (2**31))
        vec = rng.randn(DIM).astype(np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.embed(t) for t in texts])


def _make_unit_vec(seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    v = rng.randn(DIM).astype(np.float32)
    return v / np.linalg.norm(v)


def _make_deps(
    embedder: FakeEmbedder | None = None,
    config: MMemConfig | None = None,
):
    graph = MemoryGraph()
    vs = VectorStore(dimension=DIM)
    emb = embedder or FakeEmbedder()
    cfg = config or MMemConfig()
    builder = GraphBuilder(graph, vs, emb, cfg)
    return graph, vs, builder


def _simple_result(
    summary: str = "Alice joined Acme Corp in 2024.",
    entities: list[EntityInfo] | None = None,
    facet_points: list[FacetPointInfo] | None = None,
    facets: list[FacetInfo] | None = None,
    temporal_info: list[TemporalInfo] | None = None,
) -> ExtractionResult:
    return ExtractionResult(
        episode_summary=summary,
        entities=entities or [
            EntityInfo(name="Alice", entity_type="person"),
            EntityInfo(name="Acme Corp", entity_type="organization"),
        ],
        facet_points=facet_points or [
            FacetPointInfo(
                content="Alice joined Acme Corp in 2024.",
                related_entity_name="Alice",
                timestamp_text="2024",
            ),
        ],
        facets=facets or [
            FacetInfo(theme="Career", facet_point_indices=[0]),
        ],
        temporal_info=temporal_info or [
            TemporalInfo(
                subject="Alice",
                time_expression="in 2024",
                normalized_time="2024",
                relation="at",
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════
# Basic build
# ═══════════════════════════════════════════════════════════════════════


class TestBasicBuild:
    def test_build_creates_episode(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "chk_001")

        episode = graph.get_node(br.episode_id)
        assert isinstance(episode, Episode)
        assert episode.summary == "Alice joined Acme Corp in 2024."
        assert episode.source_chunk_ids == ["chk_001"]

    def test_build_creates_entities(self):
        graph, vs, builder = _make_deps()
        builder.build(_simple_result(), "chk_001")

        entities = graph.get_nodes_by_type(NodeType.ENTITY)
        names = {e.name for e in entities}
        assert "Alice" in names
        assert "Acme Corp" in names

    def test_build_creates_facet_points(self):
        graph, vs, builder = _make_deps()
        builder.build(_simple_result(), "chk_001")

        fps = graph.get_nodes_by_type(NodeType.FACET_POINT)
        assert len(fps) == 1
        assert fps[0].content == "Alice joined Acme Corp in 2024."

    def test_build_creates_facet(self):
        graph, vs, builder = _make_deps()
        builder.build(_simple_result(), "chk_001")

        facets = graph.get_nodes_by_type(NodeType.FACET)
        assert len(facets) == 1
        assert facets[0].theme == "Career"

    def test_build_result_contains_all_ids(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "chk_001")

        assert br.episode_id
        assert len(br.new_node_ids) >= 4  # episode + 2 entities + 1 fp + (maybe facet)
        assert len(br.new_edge_ids) >= 2  # at least belongs_to edges

    def test_build_creates_belongs_to_edges(self):
        graph, vs, builder = _make_deps()
        builder.build(_simple_result(), "chk_001")

        bt_edges = graph.get_edges_by_type(EdgeType.BELONGS_TO)
        assert len(bt_edges) >= 3  # entity→fp, fp→facet, facet→episode

    def test_episode_gets_timestamp_from_temporal_info(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "chk_001")

        episode = graph.get_node(br.episode_id)
        assert isinstance(episode, Episode)
        assert episode.timestamp_text == "2024"


# ═══════════════════════════════════════════════════════════════════════
# Entity dedup
# ═══════════════════════════════════════════════════════════════════════


class TestEntityDedup:
    def test_name_match_dedup(self):
        graph, vs, builder = _make_deps()
        r1 = _simple_result(
            summary="First",
            entities=[EntityInfo(name="Alice")],
            facet_points=[],
            facets=[],
        )
        r2 = _simple_result(
            summary="Second",
            entities=[EntityInfo(name="alice")],
            facet_points=[],
            facets=[],
        )
        builder.build(r1, "c1")
        builder.build(r2, "c2")

        entities = graph.get_nodes_by_type(NodeType.ENTITY)
        assert len(entities) == 1

    def test_embed_dedup_merges_similar_names(self):
        shared_vec = _make_unit_vec(42)
        embedder = FakeEmbedder({
            "Alice": shared_vec,
            "alice smith": shared_vec,
        })
        graph, vs, builder = _make_deps(embedder=embedder)

        r1 = _simple_result(
            summary="First",
            entities=[EntityInfo(name="Alice")],
            facet_points=[],
            facets=[],
        )
        builder.build(r1, "c1")

        r2 = _simple_result(
            summary="Second",
            entities=[EntityInfo(name="alice smith")],
            facet_points=[],
            facets=[],
        )
        builder.build(r2, "c2")

        entities = graph.get_nodes_by_type(NodeType.ENTITY)
        assert len(entities) == 1

    def test_embed_dedup_keeps_different_entities(self):
        graph, vs, builder = _make_deps()

        r = _simple_result(
            summary="S",
            entities=[
                EntityInfo(name="Alice"),
                EntityInfo(name="Quantum Computing"),
            ],
            facet_points=[],
            facets=[],
        )
        builder.build(r, "c1")

        entities = graph.get_nodes_by_type(NodeType.ENTITY)
        assert len(entities) == 2

    def test_same_chunk_entity_embed_dedup(self):
        shared_vec = _make_unit_vec(99)
        embedder = FakeEmbedder({
            "Dr. Zhang": shared_vec,
            "Zhang": shared_vec,
        })
        graph, vs, builder = _make_deps(embedder=embedder)

        r = _simple_result(
            summary="S",
            entities=[
                EntityInfo(name="Dr. Zhang"),
                EntityInfo(name="Zhang"),
            ],
            facet_points=[],
            facets=[],
        )
        builder.build(r, "c1")

        entities = graph.get_nodes_by_type(NodeType.ENTITY)
        assert len(entities) == 1


# ═══════════════════════════════════════════════════════════════════════
# Facet merge
# ═══════════════════════════════════════════════════════════════════════


class TestFacetMerge:
    def test_similar_facets_merge_across_chunks(self):
        shared_vec = _make_unit_vec(7)
        embedder = FakeEmbedder({
            "Career": shared_vec,
            "Career History": shared_vec,
        })
        graph, vs, builder = _make_deps(embedder=embedder)

        r1 = _simple_result(
            summary="First",
            entities=[EntityInfo(name="Alice")],
            facet_points=[FacetPointInfo(content="fp1", related_entity_name="Alice")],
            facets=[FacetInfo(theme="Career", facet_point_indices=[0])],
        )
        r2 = _simple_result(
            summary="Second",
            entities=[EntityInfo(name="Alice")],
            facet_points=[FacetPointInfo(content="fp2", related_entity_name="Alice")],
            facets=[FacetInfo(theme="Career History", facet_point_indices=[0])],
        )
        builder.build(r1, "c1")
        builder.build(r2, "c2")

        facets = graph.get_nodes_by_type(NodeType.FACET)
        assert len(facets) == 1

    def test_different_facets_stay_separate(self):
        graph, vs, builder = _make_deps()

        r = _simple_result(
            summary="S",
            entities=[EntityInfo(name="Alice")],
            facet_points=[
                FacetPointInfo(content="fp1", related_entity_name="Alice"),
                FacetPointInfo(content="fp2", related_entity_name="Alice"),
            ],
            facets=[
                FacetInfo(theme="Career", facet_point_indices=[0]),
                FacetInfo(theme="Hobbies", facet_point_indices=[1]),
            ],
        )
        builder.build(r, "c1")

        facets = graph.get_nodes_by_type(NodeType.FACET)
        assert len(facets) == 2

    def test_merged_facet_connects_to_new_episode(self):
        shared_vec = _make_unit_vec(7)
        embedder = FakeEmbedder({"Career": shared_vec, "Career Path": shared_vec})
        graph, vs, builder = _make_deps(embedder=embedder)

        r1 = _simple_result(
            summary="Ep1",
            entities=[],
            facet_points=[FacetPointInfo(content="fp1")],
            facets=[FacetInfo(theme="Career", facet_point_indices=[0])],
        )
        br1 = builder.build(r1, "c1")

        r2 = _simple_result(
            summary="Ep2",
            entities=[],
            facet_points=[FacetPointInfo(content="fp2")],
            facets=[FacetInfo(theme="Career Path", facet_point_indices=[0])],
        )
        br2 = builder.build(r2, "c2")

        facet = graph.get_nodes_by_type(NodeType.FACET)[0]
        parent_episodes = graph.get_parent_episodes(facet.id)
        ep_ids = {ep.id for ep in parent_episodes}
        assert br1.episode_id in ep_ids
        assert br2.episode_id in ep_ids


# ═══════════════════════════════════════════════════════════════════════
# Temporal edges
# ═══════════════════════════════════════════════════════════════════════


class TestTemporalEdges:
    def test_episode_temporal_chain(self):
        graph, vs, builder = _make_deps()

        r1 = _simple_result(summary="Ep1", entities=[], facet_points=[], facets=[])
        r2 = _simple_result(summary="Ep2", entities=[], facet_points=[], facets=[])
        r3 = _simple_result(summary="Ep3", entities=[], facet_points=[], facets=[])
        br1 = builder.build(r1, "c1")
        br2 = builder.build(r2, "c2")
        br3 = builder.build(r3, "c3")

        temp_edges = graph.get_edges_by_type(EdgeType.TEMPORAL)
        pairs = {(e.source_id, e.target_id) for e in temp_edges}
        assert (br1.episode_id, br2.episode_id) in pairs
        assert (br2.episode_id, br3.episode_id) in pairs

    def test_fp_temporal_chain_within_entity(self):
        graph, vs, builder = _make_deps()

        r = _simple_result(
            summary="S",
            entities=[EntityInfo(name="Alice")],
            facet_points=[
                FacetPointInfo(content="fp1", related_entity_name="Alice", timestamp_text="2022"),
                FacetPointInfo(content="fp2", related_entity_name="Alice", timestamp_text="2023"),
                FacetPointInfo(content="fp3", related_entity_name="Alice", timestamp_text="2024"),
            ],
            facets=[FacetInfo(theme="T", facet_point_indices=[0, 1, 2])],
        )
        builder.build(r, "c1")

        temp_edges = graph.get_edges_by_type(EdgeType.TEMPORAL)
        fp_temp = [e for e in temp_edges if "fp temporal" in e.description]
        assert len(fp_temp) == 2  # fp1→fp2, fp2→fp3

    def test_fp_temporal_cross_chunk(self):
        graph, vs, builder = _make_deps()

        r1 = _simple_result(
            summary="Ep1",
            entities=[EntityInfo(name="Alice")],
            facet_points=[FacetPointInfo(content="old fact", related_entity_name="Alice")],
            facets=[FacetInfo(theme="T", facet_point_indices=[0])],
        )
        builder.build(r1, "c1")

        r2 = _simple_result(
            summary="Ep2",
            entities=[EntityInfo(name="Alice")],
            facet_points=[FacetPointInfo(content="new fact", related_entity_name="Alice")],
            facets=[FacetInfo(theme="T2", facet_point_indices=[0])],
        )
        builder.build(r2, "c2")

        temp_edges = graph.get_edges_by_type(EdgeType.TEMPORAL)
        fp_temp = [e for e in temp_edges if "fp temporal" in e.description]
        assert len(fp_temp) == 1  # old→new


# ═══════════════════════════════════════════════════════════════════════
# Evolution edges
# ═══════════════════════════════════════════════════════════════════════


class TestEvolutionEdges:
    def test_evolution_chain_within_chunk(self):
        graph, vs, builder = _make_deps()

        r = _simple_result(
            summary="S",
            entities=[EntityInfo(name="Alice")],
            facet_points=[
                FacetPointInfo(content="fact A", related_entity_name="Alice"),
                FacetPointInfo(content="fact B", related_entity_name="Alice"),
                FacetPointInfo(content="fact C", related_entity_name="Alice"),
            ],
            facets=[FacetInfo(theme="T", facet_point_indices=[0, 1, 2])],
        )
        builder.build(r, "c1")

        evo_edges = graph.get_edges_by_type(EdgeType.EVOLUTION)
        assert len(evo_edges) == 2  # A→B, B→C (chain)

    def test_evolution_cross_chunk(self):
        graph, vs, builder = _make_deps()

        r1 = _simple_result(
            summary="Ep1",
            entities=[EntityInfo(name="Alice")],
            facet_points=[FacetPointInfo(content="old fact", related_entity_name="Alice")],
            facets=[FacetInfo(theme="T", facet_point_indices=[0])],
        )
        builder.build(r1, "c1")

        r2 = _simple_result(
            summary="Ep2",
            entities=[EntityInfo(name="Alice")],
            facet_points=[FacetPointInfo(content="new fact", related_entity_name="Alice")],
            facets=[FacetInfo(theme="T2", facet_point_indices=[0])],
        )
        builder.build(r2, "c2")

        evo_edges = graph.get_edges_by_type(EdgeType.EVOLUTION)
        assert len(evo_edges) == 1

    def test_no_evolution_for_first_chunk(self):
        graph, vs, builder = _make_deps()

        r = _simple_result(
            summary="S",
            entities=[EntityInfo(name="Alice")],
            facet_points=[FacetPointInfo(content="only fact", related_entity_name="Alice")],
            facets=[FacetInfo(theme="T", facet_point_indices=[0])],
        )
        builder.build(r, "c1")

        evo_edges = graph.get_edges_by_type(EdgeType.EVOLUTION)
        assert len(evo_edges) == 0


# ═══════════════════════════════════════════════════════════════════════
# Orphan FacetPoints
# ═══════════════════════════════════════════════════════════════════════


class TestOrphanFPs:
    def test_unclaimed_fp_links_directly_to_episode(self):
        graph, vs, builder = _make_deps()

        r = _simple_result(
            summary="S",
            entities=[],
            facet_points=[
                FacetPointInfo(content="claimed"),
                FacetPointInfo(content="orphan"),
            ],
            facets=[FacetInfo(theme="T", facet_point_indices=[0])],
        )
        builder.build(r, "c1")

        fps = graph.get_nodes_by_type(NodeType.FACET_POINT)
        orphan = [fp for fp in fps if fp.content == "orphan"][0]
        parent_eps = graph.get_parent_episodes(orphan.id)
        assert len(parent_eps) == 1


# ═══════════════════════════════════════════════════════════════════════
# involves_entity edges
# ═══════════════════════════════════════════════════════════════════════


class TestInvolvesEntityEdges:
    def test_entity_to_episode_edge_exists(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "chk_001")

        involves = graph.get_edges_by_type(EdgeType.INVOLVES_ENTITY)
        ep_targets = {e.target_id for e in involves if e.target_id == br.episode_id}
        assert len(ep_targets) >= 1

    def test_entity_to_facet_edge_exists(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "chk_001")

        involves = graph.get_edges_by_type(EdgeType.INVOLVES_ENTITY)
        facets = graph.get_nodes_by_type(NodeType.FACET)
        facet_ids = {f.id for f in facets}
        facet_targets = {e.target_id for e in involves if e.target_id in facet_ids}
        assert len(facet_targets) >= 1

    def test_description_format_entity_episode(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "chk_001")

        involves = graph.get_edges_by_type(EdgeType.INVOLVES_ENTITY)
        ep_edges = [e for e in involves if e.target_id == br.episode_id]
        descriptions = [e.description for e in ep_edges]
        assert any("is discussed in this episode" in d for d in descriptions)

    def test_description_format_entity_facet(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "chk_001")

        involves = graph.get_edges_by_type(EdgeType.INVOLVES_ENTITY)
        facets = graph.get_nodes_by_type(NodeType.FACET)
        facet_ids = {f.id for f in facets}
        facet_edges = [e for e in involves if e.target_id in facet_ids]
        descriptions = [e.description for e in facet_edges]
        assert any("is involved in" in d for d in descriptions)

    def test_no_duplicate_pairs(self):
        graph, vs, builder = _make_deps()
        builder.build(_simple_result(), "c1")

        involves = graph.get_edges_by_type(EdgeType.INVOLVES_ENTITY)
        pairs = [(e.source_id, e.target_id) for e in involves]
        assert len(pairs) == len(set(pairs))

    def test_involves_edges_in_build_result(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "chk_001")

        involves = graph.get_edges_by_type(EdgeType.INVOLVES_ENTITY)
        involves_ids = {e.id for e in involves}
        assert involves_ids.issubset(set(br.new_edge_ids))


# ═══════════════════════════════════════════════════════════════════════
# BuildResult tracking
# ═══════════════════════════════════════════════════════════════════════


class TestBuildResult:
    def test_already_indexed_ids(self):
        graph, vs, builder = _make_deps()
        br = builder.build(_simple_result(), "c1")

        assert len(br.entity_ids_already_indexed) >= 1
        assert len(br.facet_ids_already_indexed) >= 1

        for eid in br.entity_ids_already_indexed:
            assert vs.count("entity") > 0

    def test_episode_temporal_chain_sequential(self):
        """Episodes ingested in chronological order form a correct chain."""
        graph, vs, builder = _make_deps()

        br1 = builder.build(
            _simple_result(summary="Ep1", entities=[], facet_points=[], facets=[]),
            "c1",
        )
        br2 = builder.build(
            _simple_result(summary="Ep2", entities=[], facet_points=[], facets=[]),
            "c2",
        )

        temporal_edges = graph.get_edges_by_type(EdgeType.TEMPORAL)
        ep_temporal = [
            e for e in temporal_edges
            if e.source_id == br1.episode_id and e.target_id == br2.episode_id
        ]
        assert len(ep_temporal) == 1

    def test_episode_sorted_insertion_middle(self):
        """An Episode with an earlier timestamp is inserted in the middle."""
        from mmem.ingestion.extractor import TemporalInfo

        graph, vs, builder = _make_deps()

        r1 = _simple_result(summary="Ep 2020", entities=[], facet_points=[], facets=[])
        r1.temporal_info = [TemporalInfo(time_expression="2020", normalized_time="2020")]
        br1 = builder.build(r1, "c1")

        r3 = _simple_result(summary="Ep 2024", entities=[], facet_points=[], facets=[])
        r3.temporal_info = [TemporalInfo(time_expression="2024", normalized_time="2024")]
        br3 = builder.build(r3, "c3")

        # Now insert 2022 — should go between 2020 and 2024
        r2 = _simple_result(summary="Ep 2022", entities=[], facet_points=[], facets=[])
        r2.temporal_info = [TemporalInfo(time_expression="2022", normalized_time="2022")]
        br2 = builder.build(r2, "c2")

        temporal_edges = graph.get_edges_by_type(EdgeType.TEMPORAL)
        ep_temporal = [
            e for e in temporal_edges
            if graph.get_node(e.source_id) is not None
            and graph.get_node(e.source_id).node_type == NodeType.EPISODE
            and graph.get_node(e.target_id).node_type == NodeType.EPISODE
        ]

        sources = {e.source_id for e in ep_temporal}
        targets = {e.target_id for e in ep_temporal}

        assert br1.episode_id in sources
        assert br2.episode_id in sources and br2.episode_id in targets
        assert br3.episode_id in targets

        # 2020→2024 should NOT exist any more
        old_direct = [
            e for e in ep_temporal
            if e.source_id == br1.episode_id and e.target_id == br3.episode_id
        ]
        assert len(old_direct) == 0

        # 2020→2022 and 2022→2024 should exist
        link_1_2 = [
            e for e in ep_temporal
            if e.source_id == br1.episode_id and e.target_id == br2.episode_id
        ]
        link_2_3 = [
            e for e in ep_temporal
            if e.source_id == br2.episode_id and e.target_id == br3.episode_id
        ]
        assert len(link_1_2) == 1
        assert len(link_2_3) == 1


# ═══════════════════════════════════════════════════════════════════════
# Timestamp parsing
# ═══════════════════════════════════════════════════════════════════════


class TestTimestampParsing:
    def test_iso_date(self):
        assert _try_parse_timestamp("2024-01-15") is not None

    def test_iso_datetime(self):
        assert _try_parse_timestamp("2024-01-15T10:30:00") is not None

    def test_year_only(self):
        dt = _try_parse_timestamp("2024")
        assert dt is not None
        assert dt.year == 2024

    def test_none_input(self):
        assert _try_parse_timestamp(None) is None

    def test_empty_string(self):
        assert _try_parse_timestamp("") is None

    def test_unparseable(self):
        assert _try_parse_timestamp("last Tuesday") is None
