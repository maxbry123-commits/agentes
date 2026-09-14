"""Tests for Phase 3: path cost propagation and Episode scoring."""

import math

from mmem.config import RetrievalConfig
from mmem.core.edges import EdgeType, Edge
from mmem.retrieval.anchor_discovery import AnchorResult
from mmem.retrieval.path_scorer import EpisodeBundle, PathCandidate, score_episodes
from mmem.retrieval.query_preprocessor import PreprocessedQuery
from mmem.retrieval.subgraph_extractor import RelationshipIndex, SubgraphBundle


def _default_cfg(**overrides) -> RetrievalConfig:
    return RetrievalConfig(**overrides)


def _pq(hints: set[str] | None = None) -> PreprocessedQuery:
    return PreprocessedQuery(
        original="test query",
        vector_query="test query",
        query_type_hints=hints or {"general"},
    )


def _make_edge(src: str, tgt: str, etype: str, eid: str = "e1") -> Edge:
    return Edge(id=eid, source_id=src, target_id=tgt, edge_type=EdgeType(etype), description="test")


def _simple_index() -> RelationshipIndex:
    """
    ep1 ← fa1 ← fp1 (← ent1)
    ep1 ← fa1 ← fp2  (fp1 --temporal--> fp2, fp1 --evolution--> fp2)
    ep2 (causal neighbor of ep1)
    """
    idx = RelationshipIndex()
    idx.episode_ids = {"ep1", "ep2"}
    idx.facet_ids = {"fa1"}
    idx.point_ids = {"fp1", "fp2"}
    idx.entity_ids = {"ent1"}

    idx.facets_by_episode = {"ep1": {"fa1"}}
    idx.points_by_facet = {"fa1": {"fp1", "fp2"}}
    idx.entities_by_episode = {"ep1": {"ent1"}}
    idx.entities_by_facet = {"fa1": {"ent1"}}

    idx.temporal_fp_neighbors = {"fp1": {"fp2"}, "fp2": {"fp1"}}
    idx.causal_ep_neighbors = {"ep1": {"ep2"}, "ep2": {"ep1"}}
    idx.evolution_fp_neighbors = {"fp1": {"fp2"}, "fp2": {"fp1"}}

    idx.edge_lookup = {
        ("fp1", "fp2", "temporal"): _make_edge("fp1", "fp2", "temporal", "te1"),
        ("fp1", "fp2", "evolution"): _make_edge("fp1", "fp2", "evolution", "ev1"),
        ("ep1", "ep2", "causal"): _make_edge("ep1", "ep2", "causal", "ce1"),
    }
    return idx


class TestDirectEpisode:
    def test_direct_hit_with_penalty(self):
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"ep1": 0.2})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"ep1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        direct_paths = [p for p in ep1.all_paths if p.path_type == "direct_episode"]
        assert len(direct_paths) == 1
        assert abs(direct_paths[0].cost - (0.2 + 0.3)) < 1e-6  # 0.2 dist + 0.3 penalty

    def test_penalty_disabled(self):
        cfg = _default_cfg(enable_direct_episode_penalty=False)
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"ep1": 0.2})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"ep1"})

        bundles = score_episodes(sb, anchors, _pq(), config=cfg)
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        direct_paths = [p for p in ep1.all_paths if p.path_type == "direct_episode"]
        assert abs(direct_paths[0].cost - 0.2) < 1e-6


class TestFacetPath:
    def test_facet_direct_hit(self):
        idx = _simple_index()
        # Use 0.25 to avoid near-match discount (threshold < 0.2)
        anchors = AnchorResult(node_distances={"fa1": 0.25})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fa1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        facet_paths = [p for p in ep1.all_paths if p.path_type == "facet"]
        assert len(facet_paths) >= 1
        # cost = facet_dist(0.25) + belongs_to(0.02) + hop(0.05)
        expected = 0.25 + 0.02 + 0.05
        assert abs(facet_paths[0].cost - expected) < 1e-6


class TestPointPath:
    def test_point_via_facet(self):
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"fp1": 0.1})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fp1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        point_paths = [p for p in ep1.all_paths if p.path_type == "point"]
        assert len(point_paths) >= 1
        # fp1(0.1) → FP→Facet bt(0.02) + hop(0.05) → Facet→Ep bt(0.02) + hop(0.05)
        expected = 0.1 + 0.02 + 0.05 + 0.02 + 0.05
        assert abs(point_paths[0].cost - expected) < 1e-6


class TestEntityPath:
    def test_entity_direct_to_episode(self):
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"ent1": 0.05})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"ent1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        entity_paths = [p for p in ep1.all_paths if p.path_type == "entity"]
        assert len(entity_paths) >= 1
        # ent1(0.05) + bt(0.02) + hop(0.05)
        expected = 0.05 + 0.02 + 0.05
        assert abs(entity_paths[0].cost - expected) < 1e-6


class TestBelongsToCost:
    def test_belongs_to_uses_fixed_cost(self):
        """belongs_to edges use belongs_to_cost, not edge_miss_cost."""
        cfg = _default_cfg(belongs_to_cost=0.02, edge_miss_cost=0.9)
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"fp1": 0.1})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fp1"})

        bundles = score_episodes(sb, anchors, _pq(), config=cfg)
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        point_paths = [p for p in ep1.all_paths if p.path_type == "point"]
        # fp1→Facet: bt=0.02 (not 0.9), Facet→Ep: bt=0.02
        expected = 0.1 + 0.02 + 0.05 + 0.02 + 0.05
        assert abs(point_paths[0].cost - expected) < 1e-6


class TestTemporalBridge:
    def test_temporal_bridge_path(self):
        idx = _simple_index()
        # fp1 is anchor, fp2 is temporal neighbor → reaches ep1 via fp2→fa1→ep1
        anchors = AnchorResult(node_distances={"fp1": 0.1})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fp1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        tb_paths = [p for p in ep1.all_paths if p.path_type == "temporal_bridge"]
        assert len(tb_paths) >= 1

    def test_relation_paths_disabled(self):
        cfg = _default_cfg(enable_relation_paths=False)
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"fp1": 0.1})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fp1"})

        bundles = score_episodes(sb, anchors, _pq(), config=cfg)
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        relation_paths = [
            p for p in ep1.all_paths
            if p.path_type in ("temporal_bridge", "causal_bridge", "evolution_bridge")
        ]
        assert len(relation_paths) == 0


class TestCausalBridge:
    def test_causal_bridge_path(self):
        idx = _simple_index()
        # ep1 is anchor, ep2 is causal neighbor
        anchors = AnchorResult(node_distances={"ep1": 0.2})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"ep1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep2 = next((b for b in bundles if b.episode_id == "ep2"), None)
        assert ep2 is not None
        cb_paths = [p for p in ep2.all_paths if p.path_type == "causal_bridge"]
        assert len(cb_paths) >= 1


class TestEvolutionBridge:
    def test_evolution_bridge_path(self):
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"fp1": 0.1})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fp1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        evo_paths = [p for p in ep1.all_paths if p.path_type == "evolution_bridge"]
        assert len(evo_paths) >= 1


class TestQuerySensitiveDiscount:
    def test_temporal_discount(self):
        cfg = _default_cfg(temporal_discount=0.5)
        idx = _simple_index()
        anchors = AnchorResult(
            node_distances={"fp1": 0.1},
            edge_distances={"te1": 0.8},
        )
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fp1"})

        # Without temporal hint
        b_general = score_episodes(sb, anchors, _pq({"general"}), config=cfg)
        # With temporal hint
        b_temporal = score_episodes(sb, anchors, _pq({"temporal"}), config=cfg)

        ep1_gen = next(b for b in b_general if b.episode_id == "ep1")
        ep1_tmp = next(b for b in b_temporal if b.episode_id == "ep1")

        tb_gen = [p for p in ep1_gen.all_paths if p.path_type == "temporal_bridge"]
        tb_tmp = [p for p in ep1_tmp.all_paths if p.path_type == "temporal_bridge"]

        if tb_gen and tb_tmp:
            assert tb_tmp[0].cost < tb_gen[0].cost


class TestFacetNearMatch:
    def test_very_close_facet_gets_discount(self):
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"fa1": 0.05})  # < 0.1
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fa1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep1 = next(b for b in bundles if b.episode_id == "ep1")
        facet_paths = [p for p in ep1.all_paths if p.path_type == "facet"]
        assert len(facet_paths) >= 1
        # near-match: edge_cost=0.1, hop=0.05, facet_cost=0.05
        expected = 0.05 + 0.1 + 0.05
        assert abs(facet_paths[0].cost - expected) < 1e-6


class TestEpisodeScoreIsMin:
    def test_score_is_minimum_path(self):
        idx = _simple_index()
        anchors = AnchorResult(node_distances={"fp1": 0.1, "ep1": 0.5})
        sb = SubgraphBundle(index=idx, anchor_node_ids={"fp1", "ep1"})

        bundles = score_episodes(sb, anchors, _pq())
        ep1 = next(b for b in bundles if b.episode_id == "ep1")

        # Point path should be cheaper than direct_episode (0.1+0.02+0.05+0.02+0.05 < 0.5+0.3)
        assert ep1.score < 0.5
        all_costs = [p.cost for p in ep1.all_paths]
        assert abs(ep1.score - min(all_costs)) < 1e-9
