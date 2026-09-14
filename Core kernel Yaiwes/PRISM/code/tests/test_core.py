"""Unit tests for core data structures: nodes, edges, and MemoryGraph."""

from datetime import timezone

import pytest

from mmem.core.nodes import Entity, FacetPoint, Facet, Episode, NodeType
from mmem.core.edges import (
    Edge,
    EdgeType,
    make_belongs_to,
    make_causal,
    make_evolution,
    make_semantic,
    make_temporal,
)
from mmem.core.graph import MemoryGraph


# ── Node Tests ───────────────────────────────────────────────────────

class TestNodes:
    def test_entity_creation(self):
        e = Entity(name="张博士", entity_type="person")
        assert e.node_type == NodeType.ENTITY
        assert e.text_for_embedding == "张博士"
        assert len(e.id) == 12

    def test_facet_point_creation(self):
        fp = FacetPoint(content="张博士在2023年加入MIT")
        assert fp.node_type == NodeType.FACET_POINT
        assert fp.text_for_embedding == "张博士在2023年加入MIT"

    def test_facet_creation(self):
        f = Facet(theme="张博士的职业经历")
        assert f.node_type == NodeType.FACET
        assert f.text_for_embedding == "张博士的职业经历"

    def test_episode_creation(self):
        ep = Episode(summary="讨论了张博士的职业变动")
        assert ep.node_type == NodeType.EPISODE
        assert ep.text_for_embedding == "讨论了张博士的职业变动"

    def test_unique_ids(self):
        nodes = [Entity(name=f"e{i}") for i in range(100)]
        ids = {n.id for n in nodes}
        assert len(ids) == 100

    def test_created_at_is_utc(self):
        e = Entity(name="test")
        assert e.created_at.tzinfo is not None
        assert e.created_at.tzinfo == timezone.utc

    def test_node_eq_by_id(self):
        e1 = Entity(id="same_id", name="Alice")
        e2 = Entity(id="same_id", name="Bob")
        assert e1 == e2
        assert hash(e1) == hash(e2)

    def test_node_neq_by_id(self):
        e1 = Entity(name="Alice")
        e2 = Entity(name="Alice")
        assert e1 != e2


# ── Edge Tests ───────────────────────────────────────────────────────

class TestEdges:
    def test_belongs_to(self):
        e = make_belongs_to("child", "parent")
        assert e.edge_type == EdgeType.BELONGS_TO
        assert e.is_directed is True

    def test_semantic(self):
        e = make_semantic("a", "b", similarity=0.9)
        assert e.edge_type == EdgeType.SEMANTIC
        assert e.is_directed is False
        assert e.weight == pytest.approx(0.1)

    def test_temporal(self):
        e = make_temporal("earlier", "later")
        assert e.edge_type == EdgeType.TEMPORAL
        assert e.is_directed is True

    def test_causal(self):
        e = make_causal("cause", "effect", "A caused B", confidence=0.85)
        assert e.edge_type == EdgeType.CAUSAL
        assert e.confidence == 0.85

    def test_evolution(self):
        e = make_evolution("fp_old", "fp_new", "salary changed")
        assert e.edge_type == EdgeType.EVOLUTION
        assert e.is_directed is True

    def test_edge_created_at_is_utc(self):
        e = make_temporal("a", "b")
        assert e.created_at.tzinfo is not None
        assert e.created_at.tzinfo == timezone.utc

    def test_edge_eq_by_id(self):
        e1 = Edge(id="eid", source_id="a", target_id="b", edge_type=EdgeType.TEMPORAL)
        e2 = Edge(id="eid", source_id="c", target_id="d", edge_type=EdgeType.CAUSAL)
        assert e1 == e2
        assert hash(e1) == hash(e2)

    def test_edge_neq_by_id(self):
        e1 = Edge(source_id="a", target_id="b", edge_type=EdgeType.TEMPORAL)
        e2 = Edge(source_id="a", target_id="b", edge_type=EdgeType.TEMPORAL)
        assert e1 != e2


# ── MemoryGraph Tests ────────────────────────────────────────────────

class TestMemoryGraph:
    def _build_sample_graph(self) -> MemoryGraph:
        """
        Build a small inverted-cone graph:
          Entity("张博士") → FacetPoint → Facet → Episode
        with a temporal edge between two episodes.
        """
        g = MemoryGraph()

        ent = g.add_node(Entity(name="张博士", entity_type="person"))
        fp1 = g.add_node(FacetPoint(content="张博士在2023年加入MIT"))
        fp2 = g.add_node(FacetPoint(content="张博士在2024年发表Nature论文"))
        facet = g.add_node(Facet(theme="张博士的职业经历"))
        ep1 = g.add_node(Episode(summary="入职讨论"))
        ep2 = g.add_node(Episode(summary="发表论文"))

        # hierarchy: Entity → FacetPoint → Facet → Episode
        g.add_edge(make_belongs_to(ent.id, fp1.id, "张博士 belongs_to fp1"))
        g.add_edge(make_belongs_to(ent.id, fp2.id, "张博士 belongs_to fp2"))
        g.add_edge(make_belongs_to(fp1.id, facet.id))
        g.add_edge(make_belongs_to(fp2.id, facet.id))
        g.add_edge(make_belongs_to(facet.id, ep1.id))
        g.add_edge(make_belongs_to(facet.id, ep2.id))

        # temporal edge between episodes
        g.add_edge(make_temporal(ep1.id, ep2.id, "入职早于发表"))

        # evolution edge between facet points
        g.add_edge(make_evolution(fp1.id, fp2.id, "职业发展"))

        return g

    def test_add_and_count(self):
        g = self._build_sample_graph()
        assert g.num_nodes == 6
        # 6 belongs_to + 1 temporal + 1 evolution = 8 directed edges
        assert g.stats()["edges_by_type"]["belongs_to"] == 6
        assert g.stats()["edges_by_type"]["temporal"] == 1
        assert g.stats()["edges_by_type"]["evolution"] == 1

    def test_entity_deduplication(self):
        g = MemoryGraph()
        e1 = g.add_node(Entity(name="张博士"))
        e2 = g.add_node(Entity(name="张博士"))
        assert e1.id == e2.id
        assert g.num_nodes == 1

    def test_entity_dedup_case_insensitive(self):
        g = MemoryGraph()
        e1 = g.add_node(Entity(name="MIT"))
        e2 = g.add_node(Entity(name="mit"))
        assert e1.id == e2.id

    def test_get_entity_by_name(self):
        g = self._build_sample_graph()
        ent = g.get_entity_by_name("张博士")
        assert ent is not None
        assert ent.name == "张博士"

    def test_neighbors(self):
        g = self._build_sample_graph()
        ent = g.get_entity_by_name("张博士")
        out_neighbors = g.neighbors(ent.id, direction="out")
        assert len(out_neighbors) == 2  # two belongs_to edges to FacetPoints

    def test_k_hop(self):
        g = self._build_sample_graph()
        ent = g.get_entity_by_name("张博士")
        # 1-hop: FacetPoint nodes
        one_hop = g.k_hop_neighbors([ent.id], k=1)
        assert len(one_hop) >= 3  # entity + 2 facet_points

        # 3-hop should reach episodes
        three_hop = g.k_hop_neighbors([ent.id], k=3)
        assert len(three_hop) == 6  # all nodes reachable

    def test_parent_episodes(self):
        g = self._build_sample_graph()
        ent = g.get_entity_by_name("张博士")
        episodes = g.get_parent_episodes(ent.id)
        assert len(episodes) == 2

    def test_semantic_edge_bidirectional(self):
        g = MemoryGraph()
        n1 = g.add_node(FacetPoint(content="fact A"))
        n2 = g.add_node(FacetPoint(content="fact B"))
        g.add_edge(make_semantic(n1.id, n2.id, 0.85, "similar facts"))

        out_from_n1 = g.neighbors(n1.id, edge_types={EdgeType.SEMANTIC}, direction="out")
        out_from_n2 = g.neighbors(n2.id, edge_types={EdgeType.SEMANTIC}, direction="out")
        assert len(out_from_n1) == 1
        assert len(out_from_n2) == 1  # mirror edge

    def test_get_edges_between(self):
        g = self._build_sample_graph()
        ent = g.get_entity_by_name("张博士")
        fps = g.get_nodes_by_type(NodeType.FACET_POINT)
        for fp in fps:
            edges = g.get_edges_between(ent.id, fp.id, EdgeType.BELONGS_TO)
            assert len(edges) == 1

    def test_neighbors_both_deduplicates_undirected_semantic_edges(self):
        g = MemoryGraph()
        n1 = g.add_node(FacetPoint(content="fact A"))
        n2 = g.add_node(FacetPoint(content="fact B"))
        g.add_edge(make_semantic(n1.id, n2.id, 0.85, "similar facts"))

        both_neighbors = g.neighbors(
            n1.id,
            edge_types={EdgeType.SEMANTIC},
            direction="both",
        )
        assert len(both_neighbors) == 1

    def test_add_edge_requires_existing_nodes(self):
        g = MemoryGraph()
        with pytest.raises(ValueError, match="source/target node is missing"):
            g.add_edge(make_temporal("missing_a", "missing_b"))
        assert g.num_nodes == 0

    def test_stats(self):
        g = self._build_sample_graph()
        s = g.stats()
        assert s["nodes_by_type"]["entity"] == 1
        assert s["nodes_by_type"]["facet_point"] == 2
        assert s["nodes_by_type"]["facet"] == 1
        assert s["nodes_by_type"]["episode"] == 2

    def test_remove_node(self):
        g = self._build_sample_graph()
        ent = g.get_entity_by_name("张博士")
        g.remove_node(ent.id)
        assert g.get_entity_by_name("张博士") is None
        assert g.num_nodes == 5

    def test_remove_node_cleans_up_edges_by_type(self):
        g = MemoryGraph()
        n1 = g.add_node(Episode(summary="ep1"))
        n2 = g.add_node(Episode(summary="ep2"))
        g.add_edge(make_temporal(n1.id, n2.id))
        assert len(g.get_edges_by_type(EdgeType.TEMPORAL)) == 1

        g.remove_node(n1.id)
        assert len(g.get_edges_by_type(EdgeType.TEMPORAL)) == 0
        assert g.stats()["edges_by_type"].get("temporal", 0) == 0

    def test_remove_node_cleans_up_semantic_mirror_edges(self):
        g = MemoryGraph()
        n1 = g.add_node(FacetPoint(content="A"))
        n2 = g.add_node(FacetPoint(content="B"))
        g.add_edge(make_semantic(n1.id, n2.id, 0.9, "similar"))
        assert len(g.get_edges_by_type(EdgeType.SEMANTIC)) == 1

        g.remove_node(n1.id)
        assert len(g.get_edges_by_type(EdgeType.SEMANTIC)) == 0

    def test_remove_edge_directed(self):
        g = MemoryGraph()
        n1 = g.add_node(Episode(summary="ep1"))
        n2 = g.add_node(Episode(summary="ep2"))
        e = g.add_edge(make_temporal(n1.id, n2.id, "seq"))
        assert len(g.get_edges_by_type(EdgeType.TEMPORAL)) == 1

        g.remove_edge(e.id)
        assert len(g.get_edges_by_type(EdgeType.TEMPORAL)) == 0

    def test_remove_edge_undirected_cleans_mirror(self):
        g = MemoryGraph()
        n1 = g.add_node(FacetPoint(content="A"))
        n2 = g.add_node(FacetPoint(content="B"))
        e = g.add_edge(make_semantic(n1.id, n2.id, 0.9, "similar"))
        assert len(g.get_edges_by_type(EdgeType.SEMANTIC)) == 1

        g.remove_edge(e.id)
        assert len(g.get_edges_by_type(EdgeType.SEMANTIC)) == 0
        assert g.get_edges_between(n1.id, n2.id) == []
        assert g.get_edges_between(n2.id, n1.id) == []

    def test_remove_edge_nonexistent_is_noop(self):
        g = MemoryGraph()
        g.remove_edge("does-not-exist")

    def test_neighbors_returns_empty_for_missing_node(self):
        g = MemoryGraph()
        result = g.neighbors("nonexistent")
        assert result == []

    def test_k_hop_tolerates_missing_seed(self):
        g = MemoryGraph()
        n1 = g.add_node(Episode(summary="ep1"))
        result = g.k_hop_neighbors(["nonexistent", n1.id], k=1)
        assert n1.id in result
