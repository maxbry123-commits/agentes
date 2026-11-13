"""Tests for the hierarchical retrieval channel."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from cognithor.memory.hierarchical.models import (
    DocumentMetadata,
    DocumentTree,
    SelectedNode,
    TreeNode,
)
from cognithor.memory.hierarchical.retrieval import HierarchicalRetriever

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tree() -> DocumentTree:
    root = TreeNode(
        node_id="root",
        document_id="d1",
        parent_id=None,
        level=0,
        title="Root",
        summary="Root",
        content="Root content",
        content_hash="h0",
        token_count=5,
        children_ids=("c1",),
        position=0,
    )
    child = TreeNode(
        node_id="c1",
        document_id="d1",
        parent_id="root",
        level=1,
        title="Child",
        summary="Child summary",
        content="Child content",
        content_hash="h1",
        token_count=5,
        children_ids=(),
        position=1,
    )
    return DocumentTree(
        document_id="d1",
        source_path=Path("/tmp/test.md"),
        source_hash="abc",
        title="Test",
        root_node_id="root",
        nodes={"root": root, "c1": child},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        parser_used="MarkdownParser",
        total_tokens=10,
    )


def _mock_store(trees: list[DocumentTree] | None = None) -> MagicMock:
    store = MagicMock()
    if trees is None:
        trees = []
    store.has_any_documents.return_value = len(trees) > 0
    store.list_documents.return_value = [
        DocumentMetadata(
            document_id=t.document_id,
            title=t.title,
            source_path=str(t.source_path),
            parser_used=t.parser_used,
            total_tokens=t.total_tokens,
            node_count=len(t.nodes),
            created_at=t.created_at.isoformat(),
        )
        for t in trees
    ]
    store.load_tree.side_effect = lambda did: next((t for t in trees if t.document_id == did), None)
    return store


def _mock_selector(selected: list[SelectedNode]) -> MagicMock:
    selector = MagicMock()
    selector.select_nodes = AsyncMock(return_value=selected)
    return selector


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRetrieval:
    async def test_search_returns_results(self) -> None:
        tree = _make_tree()
        node = tree.nodes["c1"]
        selected = [SelectedNode(node=node, depth=1, reasoning="match", score=0.0)]
        store = _mock_store([tree])
        selector = _mock_selector(selected)

        retriever = HierarchicalRetriever(store, selector)
        results = await retriever.search("query")

        assert len(results) == 1
        assert results[0]["content"] == "Child content"
        assert results[0]["document_id"] == "d1"
        assert results[0]["node_title"] == "Child"

    async def test_score_calculation(self) -> None:
        tree = _make_tree()
        node = tree.nodes["c1"]
        # depth 0 -> 1/(1+0) * 0.8 = 0.8
        # depth 1 -> 1/(1+1) * 0.8 = 0.4
        # depth 2 -> 1/(1+2) * 0.8 = 0.2667
        selected = [
            SelectedNode(node=node, depth=0, reasoning="d0", score=0.0),
            SelectedNode(node=node, depth=1, reasoning="d1", score=0.0),
            SelectedNode(node=node, depth=2, reasoning="d2", score=0.0),
        ]
        store = _mock_store([tree])
        selector = _mock_selector(selected)

        retriever = HierarchicalRetriever(store, selector)
        results = await retriever.search("query")

        assert len(results) == 3
        assert abs(results[0]["score"] - 0.8) < 0.01
        assert abs(results[1]["score"] - 0.4) < 0.01
        assert abs(results[2]["score"] - 0.2667) < 0.01

    async def test_empty_store(self) -> None:
        store = _mock_store([])
        selector = _mock_selector([])

        retriever = HierarchicalRetriever(store, selector)
        results = await retriever.search("query")

        assert results == []

    async def test_source_type_hierarchical(self) -> None:
        tree = _make_tree()
        node = tree.nodes["c1"]
        selected = [SelectedNode(node=node, depth=0, reasoning="r", score=0.0)]
        store = _mock_store([tree])
        selector = _mock_selector(selected)

        retriever = HierarchicalRetriever(store, selector)
        results = await retriever.search("query")

        for r in results:
            assert r["source_type"] == "hierarchical"

    async def test_max_results_limit(self) -> None:
        tree = _make_tree()
        node = tree.nodes["c1"]
        selected = [
            SelectedNode(node=node, depth=i, reasoning=f"r{i}", score=0.0) for i in range(10)
        ]
        store = _mock_store([tree])
        selector = _mock_selector(selected)

        retriever = HierarchicalRetriever(store, selector)
        results = await retriever.search("query", max_results=3)

        assert len(results) == 3
