"""
Phase 1: Anchor discovery — multi-index vector search.

Embeds the preprocessed query and searches 6 FAISS indexes (all except
``edge_belongs_to`` which has no vectors).  Returns per-node and per-edge
best distances.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from mmem.config import RetrievalConfig, get_config
from mmem.indexing.vector_store import VectorStore
from mmem.utils.embedding import EmbeddingModel

from .query_preprocessor import PreprocessedQuery

_SKIP_INDEXES = {"edge_belongs_to"}

_EDGE_INDEXES = {"edge_relation", "edge_semantic"}


@dataclass
class AnchorResult:
    node_distances: dict[str, float] = field(default_factory=dict)
    edge_distances: dict[str, float] = field(default_factory=dict)
    hits_by_index: dict[str, list[tuple[str, float]]] = field(default_factory=dict)


def discover_anchors(
    preprocessed: PreprocessedQuery,
    vector_store: VectorStore,
    embedder: EmbeddingModel,
    config: RetrievalConfig | None = None,
) -> AnchorResult:
    """Search all relevant FAISS indexes and return anchor distances."""
    cfg = config or get_config().retrieval
    query_vec = embedder.embed(preprocessed.vector_query)
    query_vec = np.asarray(query_vec, dtype=np.float32)

    result = AnchorResult()

    for index_name in vector_store.index_names:
        if index_name in _SKIP_INDEXES:
            continue
        if not vector_store.has_index(index_name):
            continue

        hits = vector_store.search(index_name, query_vec, top_k=cfg.wide_search_top_k)
        result.hits_by_index[index_name] = hits

        is_edge = index_name in _EDGE_INDEXES
        target = result.edge_distances if is_edge else result.node_distances

        for item_id, score in hits:
            distance = 1.0 - score
            prev = target.get(item_id)
            if prev is None or distance < prev:
                target[item_id] = distance

    return result
