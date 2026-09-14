"""Tests for the PDF parser (all pymupdf interactions mocked)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cognithor.memory.hierarchical.models import ParserError, RawSection
from cognithor.memory.hierarchical.parsers.pdf import PDFParser


@pytest.fixture()
def parser() -> PDFParser:
    return PDFParser()


def _make_mock_doc(
    toc: list | None = None,
    pages: list[dict] | None = None,
    page_count: int = 1,
) -> MagicMock:
    """Build a mock fitz.Document."""
    doc = MagicMock()
    doc.get_toc.return_value = toc or []
    doc.__len__ = lambda self: page_count

    mock_pages = []
    for i in range(page_count):
        page = MagicMock()
        if pages and i < len(pages):
            page.get_text.side_effect = lambda fmt, flags=0, _p=pages[i]: (
                _p.get("text", "") if fmt == "text" else _p.get("dict", {"blocks": []})
            )
        else:
            page.get_text.return_value = ""
        mock_pages.append(page)

    doc.__getitem__ = lambda self, idx: mock_pages[idx]
    return doc


class TestTocExtraction:
    def test_toc_produces_correct_sections(self, parser: PDFParser) -> None:
        toc = [
            [1, "Introduction", 1],
            [2, "Background", 1],
            [1, "Methods", 2],
        ]
        pages = [
            {"text": "Intro text here."},
            {"text": "Methods text here."},
        ]
        mock_doc = _make_mock_doc(toc=toc, pages=pages, page_count=2)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            sections = parser.parse(b"fake-pdf", Path("doc.pdf"))

        assert len(sections) == 3
        assert sections[0].level == 1
        assert sections[0].title == "Introduction"
        assert sections[1].level == 2
        assert sections[1].title == "Background"
        assert sections[2].level == 1
        assert sections[2].title == "Methods"


class TestFontSizeHeuristic:
    def test_large_fonts_detected_as_headings(self, parser: PDFParser) -> None:
        blocks = [
            {
                "lines": [
                    {"spans": [{"text": "Big Title", "size": 24.0}]},
                    {"spans": [{"text": "Normal body text.", "size": 12.0}]},
                    {"spans": [{"text": "More body.", "size": 12.0}]},
                ]
            }
        ]
        pages = [{"text": "", "dict": {"blocks": blocks}}]
        mock_doc = _make_mock_doc(toc=[], pages=pages, page_count=1)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            sections = parser.parse(b"fake-pdf", Path("doc.pdf"))

        assert len(sections) >= 1
        assert any(s.title == "Big Title" for s in sections)


class TestPageNumbers:
    def test_page_numbers_tracked(self, parser: PDFParser) -> None:
        toc = [[1, "Chapter 1", 1], [1, "Chapter 2", 2]]
        pages = [
            {"text": "Page 1 content."},
            {"text": "Page 2 content."},
        ]
        mock_doc = _make_mock_doc(toc=toc, pages=pages, page_count=2)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            sections = parser.parse(b"fake-pdf", Path("doc.pdf"))

        assert sections[0].page == 1
        assert sections[1].page == 2


class TestCorruptPdf:
    def test_corrupt_pdf_raises_parser_error(self, parser: PDFParser) -> None:
        mock_fitz = MagicMock()
        mock_fitz.open.side_effect = RuntimeError("corrupt data")

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            with pytest.raises(ParserError, match="Failed to open PDF"):
                parser.parse(b"corrupt-data", Path("bad.pdf"))


class TestEmptyPdf:
    def test_empty_pdf(self, parser: PDFParser) -> None:
        mock_doc = _make_mock_doc(toc=[], pages=[], page_count=0)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            sections = parser.parse(b"empty-pdf", Path("empty.pdf"))

        assert sections == []


class TestNoPymupdf:
    def test_no_pymupdf_raises_parser_error(self) -> None:
        parser = PDFParser()
        # Temporarily remove fitz from sys.modules if present
        saved = sys.modules.pop("fitz", None)
        try:
            with patch.dict(sys.modules, {"fitz": None}):
                with pytest.raises(ParserError, match="pymupdf not installed"):
                    parser.parse(b"data", Path("doc.pdf"))
        finally:
            if saved is not None:
                sys.modules["fitz"] = saved


class TestSupportedExtensions:
    def test_extensions(self, parser: PDFParser) -> None:
        assert parser.supported_extensions() == frozenset({".pdf"})


class TestReturnType:
    def test_returns_raw_sections(self, parser: PDFParser) -> None:
        toc = [[1, "Title", 1]]
        pages = [{"text": "Content."}]
        mock_doc = _make_mock_doc(toc=toc, pages=pages, page_count=1)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            sections = parser.parse(b"pdf", Path("doc.pdf"))

        for s in sections:
            assert isinstance(s, RawSection)
