"""Tests for hierarchical document reasoning data models and parser factory."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cognithor.memory.hierarchical.models import (
    DocumentMetadata,
    DocumentTree,
    HierarchicalIndexError,
    NodeSelectionError,
    ParserError,
    RawSection,
    SelectedNode,
    TreeBuildError,
    TreeNode,
)
from cognithor.memory.hierarchical.parsers import get_parser

# ---------------------------------------------------------------------------
# Frozen checks
# ---------------------------------------------------------------------------


class TestFrozen:
    """All dataclasses must be immutable."""

    def test_raw_section_frozen(self) -> None:
        sec = RawSection(level=1, title="T", content="C", position=0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            sec.level = 2  # type: ignore[misc]

    def test_tree_node_frozen(self) -> None:
        node = TreeNode(
            node_id="n1",
            document_id="d1",
            parent_id=None,
            level=0,
            title="Root",
            summary="s",
            content="c",
            content_hash="h",
            token_count=10,
            children_ids=(),
            position=0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            node.title = "X"  # type: ignore[misc]

    def test_document_tree_frozen(self) -> None:
        node = TreeNode(
            node_id="n1",
            document_id="d1",
            parent_id=None,
            level=0,
            title="Root",
            summary="s",
            content="c",
            content_hash="h",
            token_count=10,
            children_ids=(),
            position=0,
        )
        tree = DocumentTree(
            document_id="d1",
            source_path=Path("test.md"),
            source_hash="abc",
            title="Doc",
            root_node_id="n1",
            nodes={"n1": node},
            created_at=datetime.now(tz=UTC),
            parser_used="MarkdownParser",
            total_tokens=10,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            tree.title = "Y"  # type: ignore[misc]

    def test_selected_node_frozen(self) -> None:
        node = TreeNode(
            node_id="n1",
            document_id="d1",
            parent_id=None,
            level=0,
            title="Root",
            summary="s",
            content="c",
            content_hash="h",
            token_count=10,
            children_ids=(),
            position=0,
        )
        sel = SelectedNode(node=node, depth=0, reasoning="relevant", score=0.9)
        with pytest.raises(dataclasses.FrozenInstanceError):
            sel.score = 0.5  # type: ignore[misc]

    def test_document_metadata_frozen(self) -> None:
        meta = DocumentMetadata(
            document_id="d1",
            title="T",
            source_path="/test.md",
            parser_used="MarkdownParser",
            total_tokens=100,
            node_count=5,
            created_at="2026-01-01T00:00:00Z",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            meta.title = "X"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------


class TestDefaults:
    def test_raw_section_page_default(self) -> None:
        sec = RawSection(level=1, title="T", content="C", position=0)
        assert sec.page is None

    def test_tree_node_metadata_default(self) -> None:
        node = TreeNode(
            node_id="n1",
            document_id="d1",
            parent_id=None,
            level=0,
            title="Root",
            summary="s",
            content="c",
            content_hash="h",
            token_count=10,
            children_ids=(),
            position=0,
        )
        assert node.metadata == {}
        assert node.page_number is None


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_parser_error_is_hierarchical_index_error(self) -> None:
        assert issubclass(ParserError, HierarchicalIndexError)

    def test_tree_build_error_is_hierarchical_index_error(self) -> None:
        assert issubclass(TreeBuildError, HierarchicalIndexError)

    def test_node_selection_error_is_hierarchical_index_error(self) -> None:
        assert issubclass(NodeSelectionError, HierarchicalIndexError)

    def test_hierarchical_index_error_is_exception(self) -> None:
        assert issubclass(HierarchicalIndexError, Exception)


# ---------------------------------------------------------------------------
# DocumentMetadata creation
# ---------------------------------------------------------------------------


class TestDocumentMetadata:
    def test_creation_with_all_fields(self) -> None:
        meta = DocumentMetadata(
            document_id="doc-42",
            title="My Report",
            source_path="/docs/report.pdf",
            parser_used="PDFParser",
            total_tokens=5000,
            node_count=25,
            created_at="2026-04-10T12:00:00Z",
        )
        assert meta.document_id == "doc-42"
        assert meta.title == "My Report"
        assert meta.source_path == "/docs/report.pdf"
        assert meta.parser_used == "PDFParser"
        assert meta.total_tokens == 5000
        assert meta.node_count == 25
        assert meta.created_at == "2026-04-10T12:00:00Z"


# ---------------------------------------------------------------------------
# Parser factory
# ---------------------------------------------------------------------------


class TestGetParser:
    def test_unsupported_extension_raises(self) -> None:
        with pytest.raises(ParserError, match="Unsupported file type: .xyz"):
            get_parser(Path("file.xyz"))

    def test_md_returns_markdown_parser(self) -> None:
        parser = get_parser(Path("readme.md"))
        assert type(parser).__name__ == "MarkdownParser"

    def test_txt_returns_plaintext_parser(self) -> None:
        parser = get_parser(Path("notes.txt"))
        assert type(parser).__name__ == "PlainTextParser"

    def test_pdf_returns_pdf_parser(self) -> None:
        parser = get_parser(Path("doc.pdf"))
        assert type(parser).__name__ == "PDFParser"

    def test_docx_returns_docx_parser(self) -> None:
        parser = get_parser(Path("doc.docx"))
        assert type(parser).__name__ == "DocxParser"

    def test_html_returns_html_parser(self) -> None:
        parser = get_parser(Path("page.html"))
        assert type(parser).__name__ == "HtmlParser"
