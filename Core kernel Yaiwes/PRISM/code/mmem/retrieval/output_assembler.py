"""
Phase 4: Output assembly.

Ranks Episode bundles, selects top-K, and assembles context text for the LLM.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Optional

from mmem.config import LLMConfig, RetrievalConfig, get_config
from mmem.core.edges import EdgeType
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Episode, Facet, FacetPoint, NodeType
from mmem.utils.llm import LLMClient

from .path_scorer import EpisodeBundle


@dataclass
class RetrievalResult:
    bundles: list[EpisodeBundle]
    context_text: str
    debug_info: dict = field(default_factory=dict)


def assemble_output(
    bundles: list[EpisodeBundle],
    graph: MemoryGraph,
    config: Optional[RetrievalConfig] = None,
    top_k: Optional[int] = None,
    display_mode: Optional[str] = None,
    chunk_store: Optional[Any] = None,
    llm_client: Optional[LLMClient] = None,
    llm_config: Optional[LLMConfig] = None,
    query: str = "",
) -> RetrievalResult:
    """Select top-K bundles and build context text.

    Args:
        chunk_store: Optional ChunkStore used in ``detail`` mode to append the
            raw source dialogue text for each episode as supplementary context.
        llm_client: Optional LLM client used for re-ranking when
            ``cfg.enable_reranking`` is set.
        llm_config: Optional LLM config required alongside ``llm_client`` for
            re-ranking.
        query: The original query string, required for re-ranking.
    """
    cfg = config or get_config().retrieval
    k = top_k or cfg.top_k
    mode = display_mode or cfg.display_mode

    top_bundles = heapq.nsmallest(k, bundles, key=lambda b: b.score)
    pre_rerank_count = len(top_bundles)

    reranked = False
    if cfg.enable_reranking and llm_client is not None and llm_config is not None and query:
        from .reranker import rerank_bundles

        top_bundles = rerank_bundles(
            question=query,
            bundles=top_bundles,
            graph=graph,
            llm_client=llm_client,
            llm_config=llm_config,
            top_n=cfg.rerank_top_n,
        )
        reranked = True

    if mode == "detail":
        context = _assemble_detail(top_bundles, graph, cfg, chunk_store=chunk_store)
    else:
        context = _assemble_summary(top_bundles, graph)

    return RetrievalResult(
        bundles=top_bundles,
        context_text=context,
        debug_info={
            "total_candidates": len(bundles),
            "top_k": k,
            "display_mode": mode,
            "reranked": reranked,
            "reranked_from": pre_rerank_count if reranked else None,
            "reranked_to": len(top_bundles) if reranked else None,
        },
    )


def _assemble_summary(bundles: list[EpisodeBundle], graph: MemoryGraph) -> str:
    parts: list[str] = []
    for i, b in enumerate(bundles, 1):
        ep = graph.get_node(b.episode_id)
        if ep is None or not isinstance(ep, Episode):
            continue
        parts.append(f"[{i}] {ep.summary}")
    return "\n".join(parts)


def _assemble_detail(
    bundles: list[EpisodeBundle],
    graph: MemoryGraph,
    cfg: RetrievalConfig,
    chunk_store: Optional[Any] = None,
) -> str:
    parts: list[str] = []
    seen_episode_ids = {b.episode_id for b in bundles}
    appended_neighbors: set[str] = set()

    for i, b in enumerate(bundles, 1):
        ep = graph.get_node(b.episode_id)
        if ep is None or not isinstance(ep, Episode):
            continue

        lines: list[str] = [f"[{i}] {ep.summary}"]

        ep_timestamp = getattr(ep, "timestamp_text", None)
        if ep_timestamp:
            lines.append(f"  [Time: {ep_timestamp}]")

        facets_shown = 0
        for neighbor_id, edge in graph.neighbors(b.episode_id):
            if facets_shown >= cfg.max_facets_per_episode:
                break
            facet = graph.get_node(neighbor_id)
            if facet is None or not isinstance(facet, Facet):
                continue
            lines.append(f"  - Facet: {facet.theme}")
            facets_shown += 1

            for fp_neighbor_id, _fp_edge in graph.neighbors(facet.id):
                fp = graph.get_node(fp_neighbor_id)
                if fp is not None and isinstance(fp, FacetPoint):
                    lines.append(f"    * {fp.content}")

        if chunk_store is not None:
            source_chunk_ids = getattr(ep, "source_chunk_ids", None) or []
            for cid in source_chunk_ids:
                raw = chunk_store.get(cid) if hasattr(chunk_store, "get") else None
                if raw:
                    lines.append(f"  [Source dialogue]:\n{raw[:600]}")

        if cfg.enable_temporal_neighbor_context:
            temporal_neighbors = graph.neighbors(
                b.episode_id,
                edge_types={EdgeType.TEMPORAL},
            )
            added_count = 0
            for nbr_id, _edge in temporal_neighbors:
                if added_count >= cfg.max_temporal_neighbors:
                    break
                if nbr_id in seen_episode_ids:
                    continue
                if nbr_id in appended_neighbors:
                    continue
                nbr_ep = graph.get_node(nbr_id)
                if nbr_ep is None or not isinstance(nbr_ep, Episode):
                    continue
                nbr_text = f"  [Adjacent context] {nbr_ep.summary}"
                if chunk_store is not None:
                    nbr_chunk_ids = getattr(nbr_ep, "source_chunk_ids", None) or []
                    for cid in nbr_chunk_ids:
                        raw = chunk_store.get(cid) if hasattr(chunk_store, "get") else None
                        if raw:
                            nbr_text += f"\n{raw[:400]}"
                lines.append(nbr_text)
                appended_neighbors.add(nbr_id)
                added_count += 1

        parts.append("\n".join(lines))

    return "\n\n".join(parts)
