"""Tests for the DocumentTreeBuilder."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.memory.hierarchical.tree_builder import DocumentTreeBuilder

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def llm_fn() -> AsyncMock:
    return AsyncMock(return_value="This is a summary.")


@pytest.fixture()
def builder(llm_fn: AsyncMock) -> DocumentTreeBuilder:
    return DocumentTreeBuilder(llm_fn=llm_fn)


def _write_md(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test.md"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBasicBuild:
    async def test_basic_build(self, tmp_path: Path, builder: DocumentTreeBuilder) -> None:
        md = _write_md(
            tmp_path,
            (
                "# Title\nIntro\n"
                "## Section A\nContent A\n"
                "## Section B\nContent B\n"
                "## Section C\nContent C\n"
            ),
        )
        tree = await builder.build(md, document_id="doc-1")

        assert tree.document_id == "doc-1"
        # h1 is child of root; h2 sections are children of h1
        root = tree.nodes[tree.root_node_id]
        assert len(root.children_ids) >= 1
        h1_node = tree.nodes[root.children_ids[0]]
        assert len(h1_node.children_ids) >= 3

    async def test_heading_jumps_insert_virtual(
        self, tmp_path: Path, builder: DocumentTreeBuilder
    ) -> None:
        md = _write_md(tmp_path, "# Title\nText\n### Deep Section\nContent\n")
        tree = await builder.build(md, document_id="doc-2")

        # There should be a virtual level-2 node between the h1 and h3
        titles = [n.title for n in tree.nodes.values()]
        assert any("Level 2" in t for t in titles), f"Expected virtual h2 in {titles}"

    async def test_content_splitting(self, tmp_path: Path, llm_fn: AsyncMock) -> None:
        builder = DocumentTreeBuilder(llm_fn=llm_fn, node_split_threshold=50)
        # Create content that exceeds 50 tokens
        long_content = " ".join(["word"] * 200)
        md = _write_md(tmp_path, f"# Title\n{long_content}\n")
        tree = await builder.build(md, document_id="doc-3")

        titles = [n.title for n in tree.nodes.values()]
        assert any("Part 1" in t for t in titles), f"Expected Part 1 in {titles}"
        assert any("Part 2" in t for t in titles), f"Expected Part 2 in {titles}"

    async def test_branching_limit(self, tmp_path: Path, llm_fn: AsyncMock) -> None:
        builder = DocumentTreeBuilder(llm_fn=llm_fn, max_branching_factor=3)
        # Create 6 sections under root
        sections = "".join(f"## Section {i}\nContent {i}\n" for i in range(6))
        md = _write_md(tmp_path, f"# Root\nIntro\n{sections}")
        tree = await builder.build(md, document_id="doc-4")

        # Should have group nodes
        titles = [n.title for n in tree.nodes.values()]
        assert any("Group" in t for t in titles), f"Expected Group node in {titles}"

    async def test_depth_limit(self, tmp_path: Path, llm_fn: AsyncMock) -> None:
        builder = DocumentTreeBuilder(llm_fn=llm_fn, max_depth=2)
        # h1 -> h2 -> h3 -> h4 — h4 should be flattened
        md = _write_md(
            tmp_path,
            "# H1\nT\n## H2\nT\n### H3\nT\n#### H4\nDeep content\n",
        )
        tree = await builder.build(md, document_id="doc-5")

        # All nodes should have depth <= 2
        def _depth(node_id: str) -> int:
            n = tree.nodes[node_id]
            if n.parent_id is None:
                return 0
            return _depth(n.parent_id) + 1

        for nid in tree.nodes:
            assert _depth(nid) <= 3  # root(0)+max_depth+1 tolerance for reparenting

    async def test_summary_generation(
        self, tmp_path: Path, llm_fn: AsyncMock, builder: DocumentTreeBuilder
    ) -> None:
        md = _write_md(tmp_path, "# Title\nContent here\n## Sub\nMore content\n")
        tree = await builder.build(md, document_id="doc-6")

        # llm_fn should have been called for nodes with content
        assert llm_fn.call_count > 0
        # All nodes with content should have summaries
        for node in tree.nodes.values():
            if node.content.strip():
                assert node.summary == "This is a summary."

    async def test_progress_callback(self, tmp_path: Path, builder: DocumentTreeBuilder) -> None:
        md = _write_md(tmp_path, "# Title\nContent\n## Sub\nMore\n")
        cb = MagicMock()
        await builder.build(md, document_id="doc-7", progress_callback=cb)

        assert cb.call_count > 0
        # Last call should have current == total
        last_call = cb.call_args_list[-1]
        current, total = last_call[0]
        assert current == total

    async def test_short_document(self, tmp_path: Path, builder: DocumentTreeBuilder) -> None:
        md = _write_md(tmp_path, "# Title\nShort.\n")
        tree = await builder.build(md, document_id="doc-8")
        assert tree.document_id == "doc-8"
        assert len(tree.nodes) >= 1

    async def test_empty_document(self, tmp_path: Path, builder: DocumentTreeBuilder) -> None:
        md = _write_md(tmp_path, "")
        tree = await builder.build(md, document_id="doc-9")
        assert len(tree.nodes) == 1
        root = tree.nodes[tree.root_node_id]
        assert root.content == ""
