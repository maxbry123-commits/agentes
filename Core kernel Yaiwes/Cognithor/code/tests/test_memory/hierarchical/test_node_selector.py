"""Tests for the LLM node selector and prompts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

from cognithor.memory.hierarchical.models import DocumentTree, TreeNode
from cognithor.memory.hierarchical.node_selector import LLMNodeSelector
from cognithor.memory.hierarchical.prompts import format_selection_prompt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tree_with_children() -> DocumentTree:
    """Tree: root -> [child-a (leaf), child-b (leaf)]."""
    root = TreeNode(
        node_id="root",
        document_id="d1",
        parent_id=None,
        level=0,
        title="Root",
        summary="Root summary",
        content="",
        content_hash="h0",
        token_count=0,
        children_ids=("child-a", "child-b"),
        position=0,
    )
    child_a = TreeNode(
        node_id="child-a",
        document_id="d1",
        parent_id="root",
        level=1,
        title="Section A",
        summary="About A",
        content="Content of section A with details.",
        content_hash="ha",
        token_count=10,
        children_ids=(),
        position=1,
    )
    child_b = TreeNode(
        node_id="child-b",
        document_id="d1",
        parent_id="root",
        level=1,
        title="Section B",
        summary="About B",
        content="Content of section B with details.",
        content_hash="hb",
        token_count=10,
        children_ids=(),
        position=2,
    )
    return DocumentTree(
        document_id="d1",
        source_path=Path("/tmp/test.md"),
        source_hash="abc",
        title="Test Doc",
        root_node_id="root",
        nodes={"root": root, "child-a": child_a, "child-b": child_b},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        parser_used="MarkdownParser",
        total_tokens=20,
    )


def _make_nested_tree() -> DocumentTree:
    """Tree: root -> mid (non-leaf) -> leaf."""
    root = TreeNode(
        node_id="root",
        document_id="d2",
        parent_id=None,
        level=0,
        title="Root",
        summary="Root summary",
        content="",
        content_hash="h0",
        token_count=0,
        children_ids=("mid",),
        position=0,
    )
    mid = TreeNode(
        node_id="mid",
        document_id="d2",
        parent_id="root",
        level=1,
        title="Middle",
        summary="Middle section",
        content="",
        content_hash="hm",
        token_count=0,
        children_ids=("leaf",),
        position=1,
    )
    leaf = TreeNode(
        node_id="leaf",
        document_id="d2",
        parent_id="mid",
        level=2,
        title="Leaf",
        summary="Leaf detail",
        content="The actual leaf content.",
        content_hash="hl",
        token_count=5,
        children_ids=(),
        position=2,
    )
    return DocumentTree(
        document_id="d2",
        source_path=Path("/tmp/test.md"),
        source_hash="def",
        title="Nested Doc",
        root_node_id="root",
        nodes={"root": root, "mid": mid, "leaf": leaf},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        parser_used="MarkdownParser",
        total_tokens=5,
    )


# ---------------------------------------------------------------------------
# Prompt tests
# ---------------------------------------------------------------------------


class TestPrompts:
    def test_format_de(self) -> None:
        result = format_selection_prompt("test query", [("n1", "Title", "Summary")], "de")
        assert "Frage" in result
        assert "n1" in result

    def test_format_en(self) -> None:
        result = format_selection_prompt("test query", [("n1", "Title", "Summary")], "en")
        assert "Query" in result
        assert "n1" in result


# ---------------------------------------------------------------------------
# Node selector tests
# ---------------------------------------------------------------------------


class TestNodeSelector:
    async def test_selects_correct_children(self) -> None:
        tree = _make_tree_with_children()
        llm_fn = AsyncMock(
            return_value=json.dumps({"selected_node_ids": ["child-a"], "reasoning": "Relevant"})
        )
        selector = LLMNodeSelector(llm_fn=llm_fn)
        results = await selector.select_nodes("find A", tree)

        assert len(results) == 1
        assert results[0].node.node_id == "child-a"

    async def test_recursive_traversal(self) -> None:
        tree = _make_nested_tree()
        # First call selects "mid" (non-leaf), second call selects "leaf"
        llm_fn = AsyncMock(
            side_effect=[
                json.dumps({"selected_node_ids": ["mid"], "reasoning": "Go deeper"}),
                json.dumps({"selected_node_ids": ["leaf"], "reasoning": "Found it"}),
            ]
        )
        selector = LLMNodeSelector(llm_fn=llm_fn)
        results = await selector.select_nodes("find leaf", tree)

        assert len(results) == 1
        assert results[0].node.node_id == "leaf"

    async def test_max_nodes_limit(self) -> None:
        tree = _make_tree_with_children()
        llm_fn = AsyncMock(
            return_value=json.dumps(
                {"selected_node_ids": ["child-a", "child-b"], "reasoning": "Both"}
            )
        )
        selector = LLMNodeSelector(llm_fn=llm_fn)
        results = await selector.select_nodes("find all", tree, max_nodes=1)

        assert len(results) == 1

    async def test_json_regex_fallback(self) -> None:
        tree = _make_tree_with_children()
        # Response with extra text around JSON
        llm_fn = AsyncMock(
            return_value=(
                'Here is my answer: {"selected_node_ids": ["child-b"], '
                '"reasoning": "B is best"} hope that helps!'
            )
        )
        selector = LLMNodeSelector(llm_fn=llm_fn)
        results = await selector.select_nodes("find B", tree)

        assert len(results) == 1
        assert results[0].node.node_id == "child-b"

    async def test_three_failures_cancel(self) -> None:
        tree = _make_tree_with_children()
        llm_fn = AsyncMock(return_value="totally invalid non-json garbage xyz")
        selector = LLMNodeSelector(llm_fn=llm_fn)
        results = await selector.select_nodes("query", tree)

        assert results == []

    async def test_empty_selection_stops(self) -> None:
        tree = _make_tree_with_children()
        llm_fn = AsyncMock(
            return_value=json.dumps({"selected_node_ids": [], "reasoning": "Nothing relevant"})
        )
        selector = LLMNodeSelector(llm_fn=llm_fn)
        results = await selector.select_nodes("obscure query", tree)

        assert results == []

    async def test_content_trimming(self) -> None:
        # Create a tree with a very long leaf
        long_content = " ".join(["word"] * 5000)
        tree = _make_tree_with_children()
        # Replace child-a content
        from dataclasses import replace

        new_a = replace(tree.nodes["child-a"], content=long_content)
        new_nodes = dict(tree.nodes)
        new_nodes["child-a"] = new_a
        tree = replace(tree, nodes=new_nodes)

        llm_fn = AsyncMock(
            return_value=json.dumps({"selected_node_ids": ["child-a"], "reasoning": "Relevant"})
        )
        selector = LLMNodeSelector(llm_fn=llm_fn)
        results = await selector.select_nodes("query", tree, max_tokens_per_node=100)

        assert len(results) == 1
        # Content should be trimmed (contain [...])
        assert "[...]" in results[0].node.content
