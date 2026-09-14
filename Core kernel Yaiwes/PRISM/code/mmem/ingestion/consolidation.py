"""
Causal consolidation — periodic LLM-based discovery of cause-effect
relationships between recent Episodes.

This module is stateless: all inputs are passed as arguments, and the only
side effect is new causal edges added to the graph and their embeddings
written to the vector store.
"""

from __future__ import annotations

import logging
from typing import Optional

from mmem.config import MMemConfig, get_config
from mmem.core.edges import EdgeType, make_causal
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Episode, NodeType
from mmem.indexing.vector_store import VectorStore
from mmem.utils.embedding import EmbeddingModel

from .extractor import Extractor

logger = logging.getLogger(__name__)


def run_consolidation(
    graph: MemoryGraph,
    vector_store: VectorStore,
    extractor: Extractor,
    embedder: EmbeddingModel,
    config: Optional[MMemConfig] = None,
) -> list[str]:
    """Discover causal edges among recent Episodes.

    Returns the IDs of newly created causal edges (may be empty).
    Never raises — LLM or validation failures are logged and swallowed
    so that the ingestion pipeline is not interrupted.
    """
    cfg = config or get_config()

    try:
        return _run(graph, vector_store, extractor, embedder, cfg)
    except Exception:
        logger.warning("Consolidation failed, returning empty", exc_info=True)
        return []


def _run(
    graph: MemoryGraph,
    vector_store: VectorStore,
    extractor: Extractor,
    embedder: EmbeddingModel,
    config: MMemConfig,
) -> list[str]:
    # Step 1: collect recent episodes
    episodes = _recent_episodes(graph, config.write.causal_consolidation_interval)
    if len(episodes) < 2:
        return []

    # Step 2: call LLM
    pairs = extractor.extract_causal(episodes)
    if not pairs:
        return []

    threshold = config.write.causal_confidence_threshold
    new_edge_ids: list[str] = []

    for pair in pairs:
        # Step 3: confidence filter
        if pair.confidence < threshold:
            continue

        # Step 4: validate endpoints exist in graph
        if not graph.has_node(pair.cause_id):
            logger.warning("Causal cause_id '%s' not in graph, skipping", pair.cause_id)
            continue
        if not graph.has_node(pair.effect_id):
            logger.warning("Causal effect_id '%s' not in graph, skipping", pair.effect_id)
            continue

        # Step 4b: duplicate edge check
        existing = graph.get_edges_between(
            pair.cause_id, pair.effect_id, EdgeType.CAUSAL,
        )
        if existing:
            continue

        # Step 5: create causal edge
        edge = make_causal(
            pair.cause_id,
            pair.effect_id,
            pair.description,
            confidence=pair.confidence,
        )
        graph.add_edge(edge)
        new_edge_ids.append(edge.id)

    # Step 6: vectorise new causal edges
    if new_edge_ids:
        _vectorize_causal_edges(graph, vector_store, embedder, new_edge_ids)

    return new_edge_ids


def _recent_episodes(graph: MemoryGraph, n: int) -> list[Episode]:
    """Return up to *n* most recent Episodes sorted by created_at."""
    all_episodes = graph.get_nodes_by_type(NodeType.EPISODE)
    episodes: list[Episode] = [
        ep for ep in all_episodes if isinstance(ep, Episode)
    ]
    episodes.sort(key=lambda ep: ep.created_at)
    return episodes[-n:]


def _vectorize_causal_edges(
    graph: MemoryGraph,
    vector_store: VectorStore,
    embedder: EmbeddingModel,
    edge_ids: list[str],
) -> None:
    ids: list[str] = []
    texts: list[str] = []
    for eid in edge_ids:
        edge = graph.get_edge(eid)
        if edge is None or not edge.description:
            continue
        ids.append(eid)
        texts.append(edge.text_for_embedding)

    if not ids:
        return
    embeddings = embedder.embed_batch(texts)
    vector_store.add("edge_relation", ids, embeddings)
