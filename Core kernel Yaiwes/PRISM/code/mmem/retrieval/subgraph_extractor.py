"""
Phase 2: Subgraph extraction.

Projects anchor hits into the graph, expands 1-hop, and builds a
``RelationshipIndex`` that pre-computes adjacency for fast path scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mmem.config import RetrievalConfig, get_config
from mmem.core.edges import Edge, EdgeType
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import NodeType

from .anchor_discovery import AnchorResult


@dataclass
class RelationshipIndex:
    """Pre-computed adjacency for path scoring."""

    episode_ids: set[str] = field(default_factory=set)
    facet_ids: set[str] = field(default_factory=set)
    point_ids: set[str] = field(default_factory=set)
    entity_ids: set[str] = field(default_factory=set)

    facets_by_episode: dict[str, set[str]] = field(default_factory=dict)
    points_by_facet: dict[str, set[str]] = field(default_factory=dict)
    entities_by_episode: dict[str, set[str]] = field(default_factory=dict)
    entities_by_facet: dict[str, set[str]] = field(default_factory=dict)

    temporal_fp_neighbors: dict[str, set[str]] = field(default_factory=dict)
    causal_ep_neighbors: dict[str, set[str]] = field(default_factory=dict)
    evolution_fp_neighbors: dict[str, set[str]] = field(default_factory=dict)

    edge_lookup: dict[tuple[str, str, str], Edge] = field(default_factory=dict)


@dataclass
class SubgraphBundle:
    index: RelationshipIndex
    anchor_node_ids: set[str] = field(default_factory=set)


def extract_subgraph(
    anchors: AnchorResult,
    graph: MemoryGraph,
    config: RetrievalConfig | None = None,
) -> SubgraphBundle:
    """Two-phase graph projection: anchor hit → 1-hop expand → build index."""
    cfg = config or get_config().retrieval

    # Phase 1: sort anchor nodes by distance, take top max_relevant_ids
    sorted_ids = sorted(anchors.node_distances.keys(), key=lambda nid: anchors.node_distances[nid])
    seed_ids = sorted_ids[: cfg.max_relevant_ids]

    # Keep track of which nodes were direct anchor hits
    anchor_set = set(seed_ids)

    # Phase 2: 1-hop expand from seeds (all edge types)
    all_node_ids: set[str] = set(seed_ids)
    for nid in seed_ids:
        if not graph.has_node(nid):
            continue
        for neighbor_id, _edge in graph.neighbors(nid):
            all_node_ids.add(neighbor_id)

    # Second expansion: for newly discovered nodes, get their neighbors too
    new_ids = all_node_ids - anchor_set
    for nid in new_ids:
        if not graph.has_node(nid):
            continue
        for neighbor_id, _edge in graph.neighbors(nid):
            all_node_ids.add(neighbor_id)

    # Build relationship index from all collected nodes
    idx = _build_relationship_index(all_node_ids, graph)

    return SubgraphBundle(index=idx, anchor_node_ids=anchor_set)


def _build_relationship_index(
    node_ids: set[str],
    graph: MemoryGraph,
) -> RelationshipIndex:
    """Walk edges among *node_ids* and populate adjacency dicts."""
    idx = RelationshipIndex()

    for nid in node_ids:
        node = graph.get_node(nid)
        if node is None:
            continue
        nt = node.node_type
        if nt == NodeType.EPISODE:
            idx.episode_ids.add(nid)
        elif nt == NodeType.FACET:
            idx.facet_ids.add(nid)
        elif nt == NodeType.FACET_POINT:
            idx.point_ids.add(nid)
        elif nt == NodeType.ENTITY:
            idx.entity_ids.add(nid)

    for nid in node_ids:
        if not graph.has_node(nid):
            continue
        for neighbor_id, edge in graph.neighbors(nid):
            if neighbor_id not in node_ids:
                continue

            src_node = graph.get_node(edge.source_id)
            tgt_node = graph.get_node(edge.target_id)
            if src_node is None or tgt_node is None:
                continue

            src_type = src_node.node_type
            tgt_type = tgt_node.node_type
            et = edge.edge_type

            key = (edge.source_id, edge.target_id, et.value)
            if key not in idx.edge_lookup:
                idx.edge_lookup[key] = edge

            if et == EdgeType.BELONGS_TO:
                _index_belongs_to(idx, src_type, tgt_type, edge.source_id, edge.target_id)

            elif et == EdgeType.TEMPORAL:
                if src_type == NodeType.FACET_POINT and tgt_type == NodeType.FACET_POINT:
                    idx.temporal_fp_neighbors.setdefault(edge.source_id, set()).add(edge.target_id)
                    idx.temporal_fp_neighbors.setdefault(edge.target_id, set()).add(edge.source_id)

            elif et == EdgeType.CAUSAL:
                if src_type == NodeType.EPISODE and tgt_type == NodeType.EPISODE:
                    idx.causal_ep_neighbors.setdefault(edge.source_id, set()).add(edge.target_id)
                    idx.causal_ep_neighbors.setdefault(edge.target_id, set()).add(edge.source_id)

            elif et == EdgeType.EVOLUTION:
                if src_type == NodeType.FACET_POINT and tgt_type == NodeType.FACET_POINT:
                    idx.evolution_fp_neighbors.setdefault(edge.source_id, set()).add(edge.target_id)
                    idx.evolution_fp_neighbors.setdefault(edge.target_id, set()).add(edge.source_id)

            elif et == EdgeType.INVOLVES_ENTITY:
                # Entity → Episode shortcut
                if src_type == NodeType.ENTITY and tgt_type == NodeType.EPISODE:
                    idx.entities_by_episode.setdefault(edge.target_id, set()).add(edge.source_id)
                # Entity → Facet shortcut
                elif src_type == NodeType.ENTITY and tgt_type == NodeType.FACET:
                    idx.entities_by_facet.setdefault(edge.target_id, set()).add(edge.source_id)

    _complete_entity_adjacency(idx)
    return idx


def _index_belongs_to(
    idx: RelationshipIndex,
    src_type: NodeType,
    tgt_type: NodeType,
    src_id: str,
    tgt_id: str,
) -> None:
    """Index a belongs_to edge (child → parent direction)."""
    # FacetPoint → Facet
    if src_type == NodeType.FACET_POINT and tgt_type == NodeType.FACET:
        idx.points_by_facet.setdefault(tgt_id, set()).add(src_id)
    # Facet → Episode
    elif src_type == NodeType.FACET and tgt_type == NodeType.EPISODE:
        idx.facets_by_episode.setdefault(tgt_id, set()).add(src_id)
    # Entity → FacetPoint (track Entity → Episode and Entity → Facet indirectly)
    elif src_type == NodeType.ENTITY and tgt_type == NodeType.FACET_POINT:
        # Entity to Episode/Facet is derived: walk Entity→FP→Facet→Episode
        pass

    # Also index reverse for entity relationships
    # In our graph: belongs_to goes Entity→FP, FP→Facet, Facet→Episode
    # We need entities_by_episode and entities_by_facet.
    # These are built by tracing Entity→FP→Facet→Episode chains.
    # We do a post-pass instead of handling it edge-by-edge.


def _complete_entity_adjacency(idx: RelationshipIndex) -> None:
    """Derive entities_by_episode and entities_by_facet from the chain."""
    # Entity → FP → Facet → Episode
    # Need a reverse map: point → entity
    entity_by_point: dict[str, set[str]] = {}
    # This requires looking at graph edges which we already processed.
    # Instead, we built point_ids and entity_ids in the index.
    # The edge_lookup has Entity→FP belongs_to edges.

    for (src, tgt, etype), _edge in idx.edge_lookup.items():
        if etype == EdgeType.BELONGS_TO.value:
            if src in idx.entity_ids and tgt in idx.point_ids:
                entity_by_point.setdefault(tgt, set()).add(src)

    for facet_id, point_set in idx.points_by_facet.items():
        for pid in point_set:
            for eid in entity_by_point.get(pid, set()):
                idx.entities_by_facet.setdefault(facet_id, set()).add(eid)

    for ep_id, facet_set in idx.facets_by_episode.items():
        for fid in facet_set:
            for eid in idx.entities_by_facet.get(fid, set()):
                idx.entities_by_episode.setdefault(ep_id, set()).add(eid)
