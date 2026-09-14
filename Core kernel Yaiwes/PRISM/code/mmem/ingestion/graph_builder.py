"""
Graph construction from structured extraction results.

Converts an ``ExtractionResult`` into nodes and edges in the ``MemoryGraph``,
handling Entity embed-dedup, Facet embed-match merging, temporal chain
building, and evolution edge creation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np

from mmem.config import MMemConfig, get_config
from mmem.core.edges import (
    EdgeType,
    make_belongs_to,
    make_evolution,
    make_involves_entity,
    make_temporal,
)
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Entity, Episode, Facet, FacetPoint, NodeType
from mmem.indexing.vector_store import VectorStore
from mmem.utils.embedding import EmbeddingModel

from .extractor import ExtractionResult, FacetInfo, FacetPointInfo

logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """What a single ``GraphBuilder.build()`` call produced."""

    episode_id: str
    new_node_ids: list[str] = field(default_factory=list)
    new_edge_ids: list[str] = field(default_factory=list)
    entity_ids_already_indexed: list[str] = field(default_factory=list)
    facet_ids_already_indexed: list[str] = field(default_factory=list)


class GraphBuilder:
    """Builds graph structure from a single chunk's extraction result."""

    def __init__(
        self,
        graph: MemoryGraph,
        vector_store: VectorStore,
        embedder: EmbeddingModel,
        config: Optional[MMemConfig] = None,
    ) -> None:
        self._graph = graph
        self._vs = vector_store
        self._embedder = embedder
        self._config = config or get_config()

    # ── Public API ────────────────────────────────────────────────────

    def build(
        self,
        result: ExtractionResult,
        chunk_id: str,
        key_sentences: Optional[list[str]] = None,
    ) -> BuildResult:
        """Process one chunk's extraction into graph nodes and edges."""
        br = BuildResult(episode_id="")

        # Step 1: Episode (sorted insertion into temporal chain)
        episode = self._build_episode(result, chunk_id, br, key_sentences=key_sentences)

        # Step 2: Entities (name-match + embed-dedup)
        entity_map = self._build_entities(result, br)

        # Step 3: FacetPoints
        fp_nodes = self._build_facet_points(result, entity_map, br)

        # Step 4: Facets (embed-match merge)
        self._build_facets(result, fp_nodes, episode, br)

        # Step 4b: involves_entity shortcut edges
        self._build_involves_entity_edges(entity_map, fp_nodes, episode, br)

        # Step 5: Temporal edges (FacetPoint level)
        self._build_fp_temporal_edges(entity_map, fp_nodes, br)

        # Step 6: Evolution edges (chain style)
        self._build_evolution_edges(entity_map, fp_nodes, br)

        return br

    # ── Step 1: Episode ───────────────────────────────────────────────

    def _build_episode(
        self,
        result: ExtractionResult,
        chunk_id: str,
        br: BuildResult,
        key_sentences: Optional[list[str]] = None,
    ) -> Episode:
        timestamp_text: str | None = None
        if result.temporal_info:
            first_ti = result.temporal_info[0]
            timestamp_text = first_ti.normalized_time or first_ti.time_expression or None

        episode = Episode(
            summary=result.episode_summary,
            source_chunk_ids=[chunk_id],
            timestamp_text=timestamp_text,
            timestamp=_try_parse_timestamp(timestamp_text),
            key_sentences=key_sentences or [],
        )
        self._graph.add_node(episode)
        br.episode_id = episode.id
        br.new_node_ids.append(episode.id)

        self._insert_episode_into_temporal_chain(episode, br)
        return episode

    def _insert_episode_into_temporal_chain(
        self, episode: Episode, br: BuildResult,
    ) -> None:
        """Insert *episode* at the correct position in the Episode temporal chain.

        Existing episodes are sorted by resolved time (timestamp if available,
        else created_at).  The new episode is inserted via bisect.  If it lands
        in the middle, the old edge between its neighbours is removed and two
        new edges are created.
        """
        existing = [
            ep for ep in self._graph.get_nodes_by_type(NodeType.EPISODE)
            if isinstance(ep, Episode) and ep.id != episode.id
        ]
        if not existing:
            return

        existing.sort(key=_ep_sort_key)
        new_key = _ep_sort_key(episode)

        # Binary search for insertion index
        lo, hi = 0, len(existing)
        while lo < hi:
            mid = (lo + hi) // 2
            if _ep_sort_key(existing[mid]) <= new_key:
                lo = mid + 1
            else:
                hi = mid
        insert_idx = lo

        if insert_idx == len(existing):
            # Append to tail
            prev_ep = existing[-1]
            edge = make_temporal(
                prev_ep.id, episode.id,
                f"episode sequence ({prev_ep.id} → {episode.id})",
            )
            self._graph.add_edge(edge)
            br.new_edge_ids.append(edge.id)
        elif insert_idx == 0:
            # Prepend to head
            next_ep = existing[0]
            edge = make_temporal(
                episode.id, next_ep.id,
                f"episode sequence ({episode.id} → {next_ep.id})",
            )
            self._graph.add_edge(edge)
            br.new_edge_ids.append(edge.id)
        else:
            # Insert in the middle: break old edge, create two new ones
            prev_ep = existing[insert_idx - 1]
            next_ep = existing[insert_idx]

            old_edges = self._graph.get_edges_between(
                prev_ep.id, next_ep.id, EdgeType.TEMPORAL,
            )
            for old_edge in old_edges:
                self._graph.remove_edge(old_edge.id)

            e1 = make_temporal(
                prev_ep.id, episode.id,
                f"episode sequence ({prev_ep.id} → {episode.id})",
            )
            e2 = make_temporal(
                episode.id, next_ep.id,
                f"episode sequence ({episode.id} → {next_ep.id})",
            )
            self._graph.add_edge(e1)
            self._graph.add_edge(e2)
            br.new_edge_ids.append(e1.id)
            br.new_edge_ids.append(e2.id)

    # ── Step 2: Entities ──────────────────────────────────────────────

    def _build_entities(
        self,
        result: ExtractionResult,
        br: BuildResult,
    ) -> dict[str, str]:
        """Returns ``{entity_name_lower: entity_id}`` for this chunk."""
        entity_map: dict[str, str] = {}
        threshold = self._config.write.entity_merge_threshold

        for info in result.entities:
            name_lower = info.name.lower()
            if name_lower in entity_map:
                continue

            existing = self._graph.get_entity_by_name(info.name)
            if existing is not None:
                entity_map[name_lower] = existing.id
                continue

            vec = self._embedder.embed(info.name)
            hits = self._vs.search("entity", vec, top_k=1)
            if hits and hits[0][1] >= threshold:
                entity_map[name_lower] = hits[0][0]
                continue

            entity = Entity(name=info.name, entity_type=info.entity_type)
            self._graph.add_node(entity)
            br.new_node_ids.append(entity.id)

            self._vs.add("entity", [entity.id], vec)
            br.entity_ids_already_indexed.append(entity.id)

            entity_map[name_lower] = entity.id

        return entity_map

    # ── Step 3: FacetPoints ───────────────────────────────────────────

    def _build_facet_points(
        self,
        result: ExtractionResult,
        entity_map: dict[str, str],
        br: BuildResult,
    ) -> list[FacetPoint]:
        """Create FacetPoint nodes and Entity→FP belongs_to edges."""
        fp_nodes: list[FacetPoint] = []

        for info in result.facet_points:
            related_entity_id = self._resolve_entity_id(
                info.related_entity_name, entity_map,
            )

            fp = FacetPoint(
                content=info.content,
                related_entity_id=related_entity_id,
                timestamp_text=info.timestamp_text,
                timestamp=_try_parse_timestamp(info.timestamp_text),
            )
            self._graph.add_node(fp)
            br.new_node_ids.append(fp.id)
            fp_nodes.append(fp)

            if related_entity_id is not None:
                edge = make_belongs_to(
                    related_entity_id,
                    fp.id,
                    f"{info.related_entity_name} → {info.content[:40]}",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)

        return fp_nodes

    # ── Step 4: Facets ────────────────────────────────────────────────

    def _build_facets(
        self,
        result: ExtractionResult,
        fp_nodes: list[FacetPoint],
        episode: Episode,
        br: BuildResult,
    ) -> None:
        threshold = self._config.write.semantic_similarity_threshold
        facets_connected_to_episode: set[str] = set()

        for info in result.facets:
            linked_fps = self._gather_linked_fps(info, fp_nodes)
            facet = self._resolve_or_create_facet(info, threshold, br)

            for fp in linked_fps:
                edge = make_belongs_to(
                    fp.id, facet.id,
                    f"{fp.content[:40]} → {facet.theme[:40]}",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)

            if facet.id not in facets_connected_to_episode:
                edge = make_belongs_to(
                    facet.id, episode.id,
                    f"{facet.theme[:40]} → {episode.summary[:40]}",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)
                facets_connected_to_episode.add(facet.id)

        # FacetPoints not claimed by any Facet still need a path to Episode.
        claimed_fp_ids = set()
        for info in result.facets:
            for idx in info.facet_point_indices:
                if 0 <= idx < len(fp_nodes):
                    claimed_fp_ids.add(fp_nodes[idx].id)

        for fp in fp_nodes:
            if fp.id not in claimed_fp_ids:
                edge = make_belongs_to(
                    fp.id, episode.id,
                    f"orphan fp → {episode.summary[:40]}",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)

    def _resolve_or_create_facet(
        self,
        info: FacetInfo,
        threshold: float,
        br: BuildResult,
    ) -> Facet:
        vec = self._embedder.embed(info.theme)
        hits = self._vs.search("facet", vec, top_k=1)
        if hits and hits[0][1] >= threshold:
            existing = self._graph.get_node(hits[0][0])
            if existing is not None and isinstance(existing, Facet):
                return existing

        facet = Facet(theme=info.theme)
        self._graph.add_node(facet)
        br.new_node_ids.append(facet.id)

        self._vs.add("facet", [facet.id], vec)
        br.facet_ids_already_indexed.append(facet.id)

        return facet

    def _gather_linked_fps(
        self,
        info: FacetInfo,
        fp_nodes: list[FacetPoint],
    ) -> list[FacetPoint]:
        out: list[FacetPoint] = []
        for idx in info.facet_point_indices:
            if 0 <= idx < len(fp_nodes):
                out.append(fp_nodes[idx])
        return out

    # ── Step 4b: involves_entity shortcut edges ─────────────────────

    def _build_involves_entity_edges(
        self,
        entity_map: dict[str, str],
        fp_nodes: list[FacetPoint],
        episode: Episode,
        br: BuildResult,
    ) -> None:
        """Build Entity→Episode and Entity→Facet shortcut edges."""
        seen: set[tuple[str, str]] = set()

        for ent_id in entity_map.values():
            ent_node = self._graph.get_node(ent_id)
            if ent_node is None:
                continue
            ent_name = getattr(ent_node, "name", ent_id)

            # Entity → Episode
            pair = (ent_id, episode.id)
            if pair not in seen:
                seen.add(pair)
                edge = make_involves_entity(
                    ent_id, episode.id,
                    f"{ent_name} is discussed in this episode",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)

        # Entity → Facet: find which entities relate to each Facet
        # through their FacetPoints
        facet_entities: dict[str, set[str]] = {}
        for fp in fp_nodes:
            if fp.related_entity_id is None:
                continue
            for neighbor_id, edge in self._graph.neighbors(fp.id, edge_types={EdgeType.BELONGS_TO}, direction="out"):
                neighbor = self._graph.get_node(neighbor_id)
                if neighbor is not None and neighbor.node_type == NodeType.FACET:
                    facet_entities.setdefault(neighbor_id, set()).add(fp.related_entity_id)

        for facet_id, ent_ids in facet_entities.items():
            facet_node = self._graph.get_node(facet_id)
            facet_theme = getattr(facet_node, "theme", facet_id) if facet_node else facet_id
            for ent_id in ent_ids:
                pair = (ent_id, facet_id)
                if pair not in seen:
                    seen.add(pair)
                    ent_node = self._graph.get_node(ent_id)
                    ent_name = getattr(ent_node, "name", ent_id) if ent_node else ent_id
                    edge = make_involves_entity(
                        ent_id, facet_id,
                        f"{ent_name} is involved in {facet_theme}",
                    )
                    self._graph.add_edge(edge)
                    br.new_edge_ids.append(edge.id)

    # ── Step 5: FP Temporal Edges ─────────────────────────────────────

    def _build_fp_temporal_edges(
        self,
        entity_map: dict[str, str],
        fp_nodes: list[FacetPoint],
        br: BuildResult,
    ) -> None:
        entity_to_new_fps: dict[str, list[FacetPoint]] = {}
        for fp in fp_nodes:
            if fp.related_entity_id and fp.related_entity_id in entity_map.values():
                entity_to_new_fps.setdefault(fp.related_entity_id, []).append(fp)

        for entity_id, new_fps in entity_to_new_fps.items():
            existing_fps = self._get_existing_fps_for_entity(entity_id, new_fps)

            if existing_fps:
                last_old = max(existing_fps, key=_fp_sort_key)
                first_new = min(new_fps, key=_fp_sort_key)
                edge = make_temporal(
                    last_old.id,
                    first_new.id,
                    f"fp temporal ({last_old.content[:30]} → {first_new.content[:30]})",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)

            sorted_new = sorted(new_fps, key=_fp_sort_key)
            for i in range(len(sorted_new) - 1):
                edge = make_temporal(
                    sorted_new[i].id,
                    sorted_new[i + 1].id,
                    f"fp temporal ({sorted_new[i].content[:30]} → {sorted_new[i+1].content[:30]})",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)

    # ── Step 6: Evolution Edges ───────────────────────────────────────

    def _build_evolution_edges(
        self,
        entity_map: dict[str, str],
        fp_nodes: list[FacetPoint],
        br: BuildResult,
    ) -> None:
        entity_to_new_fps: dict[str, list[FacetPoint]] = {}
        for fp in fp_nodes:
            if fp.related_entity_id and fp.related_entity_id in entity_map.values():
                entity_to_new_fps.setdefault(fp.related_entity_id, []).append(fp)

        for entity_id, new_fps in entity_to_new_fps.items():
            existing_fps = self._get_existing_fps_for_entity(entity_id, new_fps)
            sorted_new = sorted(new_fps, key=_fp_sort_key)

            if existing_fps:
                last_old = max(existing_fps, key=_fp_sort_key)
                edge = make_evolution(
                    last_old.id,
                    sorted_new[0].id,
                    f"evolution ({last_old.content[:30]} → {sorted_new[0].content[:30]})",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)

            for i in range(len(sorted_new) - 1):
                edge = make_evolution(
                    sorted_new[i].id,
                    sorted_new[i + 1].id,
                    f"evolution ({sorted_new[i].content[:30]} → {sorted_new[i+1].content[:30]})",
                )
                self._graph.add_edge(edge)
                br.new_edge_ids.append(edge.id)

    # ── Helpers ───────────────────────────────────────────────────────

    def _resolve_entity_id(
        self,
        name: str | None,
        entity_map: dict[str, str],
    ) -> str | None:
        if not name:
            return None
        return entity_map.get(name.lower())

    def _get_existing_fps_for_entity(
        self,
        entity_id: str,
        exclude: list[FacetPoint],
    ) -> list[FacetPoint]:
        """Find FacetPoints already in the graph for *entity_id*, excluding *exclude*."""
        exclude_ids = {fp.id for fp in exclude}
        out: list[FacetPoint] = []
        for nbr_id, edge in self._graph.neighbors(
            entity_id,
            edge_types={EdgeType.BELONGS_TO},
            direction="out",
        ):
            if nbr_id in exclude_ids:
                continue
            node = self._graph.get_node(nbr_id)
            if isinstance(node, FacetPoint):
                out.append(node)
        return out


# ── Module-level helpers ──────────────────────────────────────────────


def _try_parse_timestamp(text: str | None) -> datetime | None:
    """Best-effort ISO-8601 parse. Returns ``None`` on failure."""
    if not text:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def _ep_sort_key(ep: Episode) -> tuple[int, datetime]:
    """Sort key for Episodes: prefer parsed timestamp, fall back to created_at."""
    has_ts = ep.timestamp is not None
    return (0 if has_ts else 1, ep.timestamp or ep.created_at)


def _fp_sort_key(fp: FacetPoint) -> tuple[int, datetime]:
    """Sort key: prefer parsed timestamp, fall back to created_at."""
    has_ts = fp.timestamp is not None
    return (0 if has_ts else 1, fp.timestamp or fp.created_at)
