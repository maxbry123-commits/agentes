"""Manager for hierarchical document indexing and retrieval."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from cognithor.memory.hierarchical.models import DocumentMetadata, DocumentTree
    from cognithor.memory.hierarchical.retrieval import HierarchicalRetriever
    from cognithor.memory.hierarchical.tree_builder import DocumentTreeBuilder
    from cognithor.memory.hierarchical.tree_store import TreeStore

logger = logging.getLogger(__name__)


class HierarchicalIndexManager:
    """High-level API for indexing, removing, and listing hierarchical documents."""

    def __init__(
        self,
        tree_store: TreeStore,
        tree_builder: DocumentTreeBuilder,
        retriever: HierarchicalRetriever,
    ) -> None:
        self._store = tree_store
        self._builder = tree_builder
        self._retriever = retriever
        self._lock = asyncio.Lock()

    async def index_document(
        self,
        source_path: Path,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentTree:
        """Build a tree from *source_path*, save it to the store, and return it."""
        async with self._lock:
            tree = await self._builder.build(
                source_path,
                document_id=document_id,
                metadata=metadata,
            )
            self._store.save_tree(tree)
            logger.debug(
                "hierarchical_indexed: %s (%d nodes)",
                tree.document_id,
                len(tree.nodes),
            )
            return tree

    async def remove_document(self, document_id: str) -> None:
        """Delete a document and all its nodes from the store."""
        self._store.delete_tree(document_id)
        logger.debug("hierarchical_removed: %s", document_id)

    async def list_documents(self) -> list[DocumentMetadata]:
        """Return lightweight metadata for every indexed document."""
        return self._store.list_documents()

    async def reindex_document(self, document_id: str) -> DocumentTree:
        """Reload and re-index an existing document.

        Reads the source_path from the existing tree, deletes the old tree,
        builds a new one, and saves it.
        """
        existing = self._store.load_tree(document_id)
        if existing is None:
            msg = f"Document not found: {document_id}"
            raise ValueError(msg)

        source_path = existing.source_path

        async with self._lock:
            self._store.delete_tree(document_id)
            tree = await self._builder.build(source_path, document_id=document_id)
            self._store.save_tree(tree)
            logger.debug(
                "hierarchical_reindexed: %s (%d nodes)",
                tree.document_id,
                len(tree.nodes),
            )
            return tree
