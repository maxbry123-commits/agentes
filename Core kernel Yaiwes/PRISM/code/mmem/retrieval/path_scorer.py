"""
Phase 3: Path cost propagation and Episode scoring.

Enumerates all legal path templates (5 backbone + 3 relation bridges),
computes per-path cost, and assigns each Episode its min-cost score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mmem.config import RetrievalConfig, get_config
from mmem.core.edges import EdgeType

from .anchor_discovery import AnchorResult
from .query_preprocessor import PreprocessedQuery
from .subgraph_extractor import RelationshipIndex, SubgraphBundle

INF = float("inf")


# ── Data classes ──────────────────────────────────────────────────────


@dataclass
class PathCandidate:
    path_type: str
    cost: float
    anchor_id: str
    intermediate_ids: list[str]
    episode_id: str


@dataclass
class EpisodeBundle:
    episode_id: str
    score: float
    best_path: str
    best_path_detail: list[str] = field(default_factory=list)
    all_paths: list[PathCandidate] = field(default_factory=list)


# ── Public API ────────────────────────────────────────────────────────


def score_episodes(
    subgraph: SubgraphBundle,
    anchors: AnchorResult,
    preprocessed: PreprocessedQuery,
    config: RetrievalConfig | None = None,
) -> list[EpisodeBundle]:
    """Score every Episode reachable in *subgraph* and return bundles."""
    cfg = config or get_config().retrieval
    idx = subgraph.index
    nd = anchors.node_distances
    ed = anchors.edge_distances
    hints = preprocessed.query_type_hints

    # Pre-compute facet costs (direct + via FacetPoint + via Entity)
    facet_cost, facet_best_from = _compute_facet_costs(idx, nd, ed, hints, cfg)

    bundles: list[EpisodeBundle] = []

    # Iterate episodes in sorted order so that tie-breaking in downstream
    # `heapq.nsmallest` (which falls back to insertion order for equal keys)
    # is deterministic. RelationshipIndex.episode_ids is a `set[str]`, whose
    # iteration depends on PYTHONHASHSEED; without sort the top-K bundle
    # selection becomes non-reproducible across processes on tied scores.
    for ep_id in sorted(idx.episode_ids):
        paths: list[PathCandidate] = []

        # A. Backbone paths
        _add_direct_episode(paths, ep_id, nd, cfg)
        _add_via_facet(paths, ep_id, idx, nd, ed, facet_cost, facet_best_from, hints, cfg)
        _add_via_entity(paths, ep_id, idx, nd, ed, hints, cfg)

        # B. Relation bridge paths
        if cfg.enable_relation_paths:
            _add_temporal_bridge(paths, ep_id, idx, nd, ed, hints, cfg)
            _add_causal_bridge(paths, ep_id, idx, nd, ed, hints, cfg)
            _add_evolution_bridge(paths, ep_id, idx, nd, ed, hints, cfg)

        if not paths:
            continue

        best = min(paths, key=lambda p: p.cost)
        bundles.append(
            EpisodeBundle(
                episode_id=ep_id,
                score=best.cost,
                best_path=best.path_type,
                best_path_detail=[best.anchor_id] + best.intermediate_ids + [ep_id],
                all_paths=paths,
            )
        )

    return bundles


# ── Cost helpers ──────────────────────────────────────────────────────


def _node_dist(nd: dict[str, float], nid: str) -> float:
    return nd.get(nid, INF)


def _edge_cost_for(
    idx: RelationshipIndex,
    src: str,
    tgt: str,
    edge_type: EdgeType,
    ed: dict[str, float],
    hints: set[str],
    cfg: RetrievalConfig,
) -> float:
    """Return the cost of traversing the edge from *src* to *tgt*."""
    if edge_type == EdgeType.BELONGS_TO:
        return cfg.belongs_to_cost

    edge = idx.edge_lookup.get((src, tgt, edge_type.value))
    if edge is None:
        edge = idx.edge_lookup.get((tgt, src, edge_type.value))

    if edge is not None and edge.id in ed:
        base = ed[edge.id]
    else:
        base = cfg.edge_miss_cost

    if cfg.enable_query_sensitive_cost:
        base = _adjusted_edge_cost(edge_type, base, hints, cfg)

    return base


def _adjusted_edge_cost(
    edge_type: EdgeType,
    base_cost: float,
    hints: set[str],
    cfg: RetrievalConfig,
) -> float:
    if edge_type == EdgeType.TEMPORAL and "temporal" in hints:
        return base_cost * cfg.temporal_discount
    if edge_type == EdgeType.CAUSAL and "causal" in hints:
        return base_cost * cfg.causal_discount
    if edge_type == EdgeType.EVOLUTION and "temporal" in hints:
        return base_cost * cfg.evolution_discount
    return base_cost


def _facet_near_match(
    facet_distance: float,
    base_edge_cost: float,
    base_hop_cost: float,
) -> tuple[float, float]:
    """Apply Facet near-perfect match discount."""
    if facet_distance < 0.1:
        return 0.1, 0.05
    if facet_distance < 0.2:
        return base_edge_cost * 0.3, base_hop_cost * 0.3
    return base_edge_cost, base_hop_cost


# ── Facet cost pre-computation ────────────────────────────────────────


def _compute_facet_costs(
    idx: RelationshipIndex,
    nd: dict[str, float],
    ed: dict[str, float],
    hints: set[str],
    cfg: RetrievalConfig,
) -> tuple[dict[str, float], dict[str, tuple[str, str, float]]]:
    """Return (facet_cost, facet_best_from) dicts."""
    facet_cost: dict[str, float] = {}
    facet_best_from: dict[str, tuple[str, str, float]] = {}

    for fid in idx.facet_ids:
        best = _node_dist(nd, fid)
        facet_best_from[fid] = ("direct", fid, best)

        # Via FacetPoint
        for pid in idx.points_by_facet.get(fid, set()):
            pd = _node_dist(nd, pid)
            if math.isinf(pd):
                continue
            ec = _edge_cost_for(idx, pid, fid, EdgeType.BELONGS_TO, ed, hints, cfg)
            c = pd + ec + cfg.hop_cost
            if c < best:
                best = c
                facet_best_from[fid] = ("point", pid, c)

        # Via Entity (Entity→Facet)
        for eid in idx.entities_by_facet.get(fid, set()):
            entity_d = _node_dist(nd, eid)
            if math.isinf(entity_d):
                continue
            ec = cfg.belongs_to_cost
            c = entity_d + ec + cfg.hop_cost
            if c < best:
                best = c
                facet_best_from[fid] = ("entity_facet", eid, c)

        facet_cost[fid] = best

    return facet_cost, facet_best_from


# ── Backbone path builders ────────────────────────────────────────────


def _add_direct_episode(
    paths: list[PathCandidate],
    ep_id: str,
    nd: dict[str, float],
    cfg: RetrievalConfig,
) -> None:
    d = _node_dist(nd, ep_id)
    if math.isinf(d):
        return
    penalty = cfg.direct_episode_penalty if cfg.enable_direct_episode_penalty else 0.0
    paths.append(PathCandidate("direct_episode", d + penalty, ep_id, [], ep_id))


def _add_via_facet(
    paths: list[PathCandidate],
    ep_id: str,
    idx: RelationshipIndex,
    nd: dict[str, float],
    ed: dict[str, float],
    facet_cost: dict[str, float],
    facet_best_from: dict[str, tuple[str, str, float]],
    hints: set[str],
    cfg: RetrievalConfig,
) -> None:
    for fid in idx.facets_by_episode.get(ep_id, set()):
        fc = facet_cost.get(fid, INF)
        if math.isinf(fc):
            continue

        base_ec = _edge_cost_for(idx, fid, ep_id, EdgeType.BELONGS_TO, ed, hints, cfg)
        base_hc = cfg.hop_cost

        facet_d = _node_dist(nd, fid)
        eff_ec, eff_hc = _facet_near_match(facet_d, base_ec, base_hc)

        total = fc + eff_ec + eff_hc
        src_kind, src_id, _ = facet_best_from.get(fid, ("direct", fid, fc))

        if src_kind == "point":
            ptype = "point"
            intermediates = [src_id, fid]
        elif src_kind == "entity_facet":
            ptype = "entity_facet"
            intermediates = [src_id, fid]
        else:
            ptype = "facet"
            intermediates = [fid]

        anchor = src_id if src_kind != "direct" else fid
        paths.append(PathCandidate(ptype, total, anchor, intermediates, ep_id))


def _add_via_entity(
    paths: list[PathCandidate],
    ep_id: str,
    idx: RelationshipIndex,
    nd: dict[str, float],
    ed: dict[str, float],
    hints: set[str],
    cfg: RetrievalConfig,
) -> None:
    for eid in idx.entities_by_episode.get(ep_id, set()):
        d = _node_dist(nd, eid)
        if math.isinf(d):
            continue
        ec = cfg.belongs_to_cost
        total = d + ec + cfg.hop_cost
        paths.append(PathCandidate("entity", total, eid, [eid], ep_id))


# ── Relation bridge path builders ─────────────────────────────────────


def _add_temporal_bridge(
    paths: list[PathCandidate],
    ep_id: str,
    idx: RelationshipIndex,
    nd: dict[str, float],
    ed: dict[str, float],
    hints: set[str],
    cfg: RetrievalConfig,
) -> None:
    """FP → temporal → FP' → Facet → Episode  (3 hops)."""
    for fid in idx.facets_by_episode.get(ep_id, set()):
        for fp_prime in idx.points_by_facet.get(fid, set()):
            for fp_anchor in idx.temporal_fp_neighbors.get(fp_prime, set()):
                d = _node_dist(nd, fp_anchor)
                if math.isinf(d):
                    continue
                ec_temporal = _edge_cost_for(idx, fp_anchor, fp_prime, EdgeType.TEMPORAL, ed, hints, cfg)
                ec_bt1 = cfg.belongs_to_cost  # FP' → Facet
                ec_bt2 = cfg.belongs_to_cost  # Facet → Episode
                total = d + ec_temporal + ec_bt1 + ec_bt2 + cfg.hop_cost * 3
                paths.append(PathCandidate(
                    "temporal_bridge", total, fp_anchor,
                    [fp_anchor, fp_prime, fid], ep_id,
                ))


def _add_causal_bridge(
    paths: list[PathCandidate],
    ep_id: str,
    idx: RelationshipIndex,
    nd: dict[str, float],
    ed: dict[str, float],
    hints: set[str],
    cfg: RetrievalConfig,
) -> None:
    """Episode → causal → Episode'  (1 hop)."""
    for ep_anchor in idx.causal_ep_neighbors.get(ep_id, set()):
        d = _node_dist(nd, ep_anchor)
        if math.isinf(d):
            continue
        ec = _edge_cost_for(idx, ep_anchor, ep_id, EdgeType.CAUSAL, ed, hints, cfg)
        total = d + ec + cfg.hop_cost
        paths.append(PathCandidate(
            "causal_bridge", total, ep_anchor,
            [ep_anchor], ep_id,
        ))


def _add_evolution_bridge(
    paths: list[PathCandidate],
    ep_id: str,
    idx: RelationshipIndex,
    nd: dict[str, float],
    ed: dict[str, float],
    hints: set[str],
    cfg: RetrievalConfig,
) -> None:
    """FP → evolution → FP' → Facet → Episode  (3 hops)."""
    for fid in idx.facets_by_episode.get(ep_id, set()):
        for fp_prime in idx.points_by_facet.get(fid, set()):
            for fp_anchor in idx.evolution_fp_neighbors.get(fp_prime, set()):
                d = _node_dist(nd, fp_anchor)
                if math.isinf(d):
                    continue
                ec_evo = _edge_cost_for(idx, fp_anchor, fp_prime, EdgeType.EVOLUTION, ed, hints, cfg)
                ec_bt1 = cfg.belongs_to_cost
                ec_bt2 = cfg.belongs_to_cost
                total = d + ec_evo + ec_bt1 + ec_bt2 + cfg.hop_cost * 3
                paths.append(PathCandidate(
                    "evolution_bridge", total, fp_anchor,
                    [fp_anchor, fp_prime, fid], ep_id,
                ))
