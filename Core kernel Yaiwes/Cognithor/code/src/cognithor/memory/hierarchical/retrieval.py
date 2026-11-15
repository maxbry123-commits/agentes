"""Hierarchical retrieval channel — searches indexed document trees."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cognithor.memory.hierarchical.node_selector import LLMNodeSelector
    from cognithor.memory.hierarchical.tree_store import TreeStore

logger = logging.getLogger(__name__)

_DEFAULT_LLM_CONFIDENCE = 0.8


class HierarchicalRetriever:
    """Search across all indexed document trees using LLM-driven node selection."""

    def __init__(self, tree_store: TreeStore, node_selector: LLMNodeSelector) -> None:
        self._store = tree_store
        self._selector = node_selector

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search all stored trees and return scored results.

        Each result is a dict with keys:
        ``content``, ``score``, ``source_type``, ``document_id``, ``node_title``.
        """
        if not self._store.has_any_documents():
            return []

        docs = self._store.list_documents()
        all_results: list[dict[str, Any]] = []

        for doc_meta in docs:
            tree = self._store.load_tree(doc_meta.document_id)
            if tree is None:
                continue

            try:
                selected = await self._selector.select_nodes(query, tree)
            except Exception:
                logger.exception("Node selection failed for %s", doc_meta.document_id)
                continue

            for sn in selected:
                score = (1.0 / (1 + sn.depth)) * _DEFAULT_LLM_CONFIDENCE
                all_results.append(
                    {
                        "content": sn.node.content,
                        "score": score,
                        "source_type": "hierarchical",
                        "document_id": tree.document_id,
                        "node_title": sn.node.title,
                    }
                )

        all_results.sort(key=lambda r: r["score"], reverse=True)
        return all_results[:max_results]
