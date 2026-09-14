"""
Bundle Search — top-level orchestrator.

Ties together all four retrieval phases into a single synchronous call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from mmem.config import MMemConfig, get_config
from mmem.core.graph import MemoryGraph
from mmem.indexing.vector_store import VectorStore
from mmem.utils.embedding import EmbeddingModel
from mmem.utils.llm import LLMClient

from .anchor_discovery import discover_anchors
from .output_assembler import RetrievalResult, assemble_output
from .path_scorer import score_episodes
from .query_decomposer import decompose_query
from .query_preprocessor import preprocess_query
from .subgraph_extractor import extract_subgraph

if TYPE_CHECKING:
    from mmem.retrieval.intent_classifier import IntentClassifier

_EMPTY = RetrievalResult(bundles=[], context_text="", debug_info={})


def bundle_search(
    query: str,
    graph: MemoryGraph,
    vector_store: VectorStore,
    embedder: EmbeddingModel,
    config: Optional[MMemConfig] = None,
    top_k: int = 5,
    display_mode: str = "summary",
    chunk_store: Optional[Any] = None,
    llm_client: Optional[LLMClient] = None,
    intent_classifier: Optional["IntentClassifier"] = None,
) -> RetrievalResult:
    """Bundle Search main entry point.

    Args:
        chunk_store: Optional ChunkStore. When provided and ``display_mode`` is
            ``"detail"``, the raw source dialogue for each episode is appended
            to the generated context for richer LLM grounding.
        llm_client: Optional LLM client used by Phase 1b (Query Decomposition)
            and Phase 4 (Re-ranking). When omitted, both stages are no-ops
            regardless of the corresponding feature flags.
        intent_classifier: Optional Round-5 hybrid IntentClassifier singleton.
            Only consulted when ``cfg.intent_classifier_mode == "hybrid"``.
            Must be shared across queries — the prototype embedding index
            must not be rebuilt per call.
    """
    full_cfg = config or get_config()
    cfg = full_cfg.retrieval

    # Phase 0
    preprocessed = preprocess_query(query, cfg, intent_classifier=intent_classifier)

    # Phase 1
    anchors = discover_anchors(preprocessed, vector_store, embedder, cfg)

    # Phase 1b (optional): Query Decomposition.
    # Sub-queries each run anchor discovery and merge into the primary anchor
    # set (taking the minimum distance per node/edge).  The original query's
    # anchors are always preserved.
    if cfg.enable_query_decomposition and llm_client is not None:
        sub_queries = decompose_query(query, llm_client, full_cfg.llm)
        for sub_q in sub_queries:
            sub_preprocessed = preprocess_query(
                sub_q, cfg, intent_classifier=intent_classifier
            )
            sub_anchors = discover_anchors(sub_preprocessed, vector_store, embedder, cfg)
            for nid, dist in sub_anchors.node_distances.items():
                prev = anchors.node_distances.get(nid)
                if prev is None or dist < prev:
                    anchors.node_distances[nid] = dist
            for eid, dist in sub_anchors.edge_distances.items():
                prev = anchors.edge_distances.get(eid)
                if prev is None or dist < prev:
                    anchors.edge_distances[eid] = dist

    if not anchors.node_distances:
        return _EMPTY

    # Phase 2
    subgraph = extract_subgraph(anchors, graph, cfg)

    if not subgraph.index.episode_ids:
        return _EMPTY

    # Phase 3
    bundles = score_episodes(subgraph, anchors, preprocessed, cfg)

    if not bundles:
        return _EMPTY

    # Phase 4 — pass llm_client/llm_config/query so Re-ranking can run when
    # enabled.  ``full_cfg.llm`` is always non-empty thanks to the
    # ``config or get_config()`` fallback above; do NOT gate it on ``config``.
    return assemble_output(
        bundles,
        graph,
        cfg,
        top_k=top_k,
        display_mode=display_mode,
        chunk_store=chunk_store,
        llm_client=llm_client,
        llm_config=full_cfg.llm,
        query=query,
    )
