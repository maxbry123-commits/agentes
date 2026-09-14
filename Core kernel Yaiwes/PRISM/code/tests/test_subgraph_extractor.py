"""Tests for Phase 2: subgraph extraction + RelationshipIndex."""

from mmem.config import RetrievalConfig
from mmem.core.edges import EdgeType, make_belongs_to, make_causal, make_evolution, make_temporal
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Entity, Episode, Facet, FacetPoint
from mmem.retrieval.anchor_discovery import AnchorResult
from mmem.retrieval.subgraph_extractor import SubgraphBundle, extract_subgraph


def _build_mini_graph():
    """Build a small graph: Entity→FP→Facet→Episode with relation edges."""
    g = MemoryGraph()

    ep1 = g.add_node(Episode(summary="Alice joined Acme in 2020"))
    ep2 = g.add_node(Episode(summary="Alice left Acme in 2024"))
    fa1 = g.add_node(Facet(theme="career"))
    fp1 = g.add_node(FacetPoint(content="joined Acme"))
    fp2 = g.add_node(FacetPoint(content="left Acme"))
    ent = g.add_node(Entity(name="Alice"))

    g.add_edge(make_belongs_to(ent.id, fp1.id))
    g.add_edge(make_belongs_to(ent.id, fp2.id))
    g.add_edge(make_belongs_to(fp1.id, fa1.id))
    g.add_edge(make_belongs_to(fp2.id, fa1.id))
    g.add_edge(make_belongs_to(fa1.id, ep1.id))
    g.add_edge(make_belongs_to(fa1.id, ep2.id))

    g.add_edge(make_temporal(fp1.id, fp2.id, "fp temporal"))
    g.add_edge(make_temporal(ep1.id, ep2.id, "ep temporal"))
    g.add_edge(make_evolution(fp1.id, fp2.id, "career evolution"))
    causal_edge = make_causal(ep1.id, ep2.id, "joining led to leaving", confidence=0.8)
    g.add_edge(causal_edge)

    return g, ep1, ep2, fa1, fp1, fp2, ent


class TestBasicExtraction:
    def test_expands_from_anchor(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={fp1.id: 0.1})

        sb = extract_subgraph(anchors, g)
        idx = sb.index

        assert ep1.id in idx.episode_ids or ep2.id in idx.episode_ids
        assert fa1.id in idx.facet_ids
        assert fp1.id in idx.point_ids

    def test_anchor_set_tracked(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={fp1.id: 0.1, ent.id: 0.2})

        sb = extract_subgraph(anchors, g)
        assert fp1.id in sb.anchor_node_ids
        assert ent.id in sb.anchor_node_ids


class TestRelationshipIndex:
    def test_facets_by_episode(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={fp1.id: 0.1})

        idx = extract_subgraph(anchors, g).index
        assert fa1.id in idx.facets_by_episode.get(ep1.id, set())

    def test_points_by_facet(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={fp1.id: 0.1})

        idx = extract_subgraph(anchors, g).index
        assert fp1.id in idx.points_by_facet.get(fa1.id, set())

    def test_entities_by_facet(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={ent.id: 0.1})

        idx = extract_subgraph(anchors, g).index
        assert ent.id in idx.entities_by_facet.get(fa1.id, set())

    def test_entities_by_episode(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        # Anchor on FP so that 2-hop expansion reaches Entity, Facet, and Episode
        anchors = AnchorResult(node_distances={fp1.id: 0.1})

        idx = extract_subgraph(anchors, g).index
        assert ent.id in idx.entities_by_episode.get(ep1.id, set())


class TestRelationEdges:
    def test_temporal_fp_neighbors(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={fp1.id: 0.1})

        idx = extract_subgraph(anchors, g).index
        assert fp2.id in idx.temporal_fp_neighbors.get(fp1.id, set())

    def test_causal_ep_neighbors(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={ep1.id: 0.1})

        idx = extract_subgraph(anchors, g).index
        assert ep2.id in idx.causal_ep_neighbors.get(ep1.id, set())

    def test_evolution_fp_neighbors(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={fp1.id: 0.1})

        idx = extract_subgraph(anchors, g).index
        assert fp2.id in idx.evolution_fp_neighbors.get(fp1.id, set())


class TestEdgeLookup:
    def test_edge_lookup_populated(self):
        g, ep1, ep2, fa1, fp1, fp2, ent = _build_mini_graph()
        anchors = AnchorResult(node_distances={fp1.id: 0.1})

        idx = extract_subgraph(anchors, g).index
        assert len(idx.edge_lookup) > 0


class TestMaxRelevantIds:
    def test_truncation(self):
        g = MemoryGraph()
        nodes = [g.add_node(FacetPoint(content=f"fp{i}")) for i in range(10)]
        anchors = AnchorResult(
            node_distances={n.id: float(i) * 0.1 for i, n in enumerate(nodes)}
        )
        cfg = RetrievalConfig(max_relevant_ids=50)
        sb = extract_subgraph(anchors, g, config=cfg)
        assert len(sb.anchor_node_ids) <= 10
