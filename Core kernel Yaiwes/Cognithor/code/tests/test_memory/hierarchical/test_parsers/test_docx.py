"""Tests for the DOCX parser (all python-docx interactions mocked)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from xml.etree.ElementTree import Element, SubElement

import pytest

from cognithor.memory.hierarchical.models import ParserError
from cognithor.memory.hierarchical.parsers.docx import DocxParser


@pytest.fixture()
def parser() -> DocxParser:
    return DocxParser()


def _make_paragraph(
    text: str, style_name: str = "Normal", bold: bool = False, font_size: int | None = None
) -> MagicMock:
    """Create a mock python-docx Paragraph."""
    para = MagicMock()
    para.text = text
    para.style = MagicMock()
    para.style.name = style_name

    run = MagicMock()
    run.bold = bold
    run.font = MagicMock()
    run.font.size = font_size
    para.runs = [run]

    # Give it a unique element
    elem = Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")
    para._element = elem
    para._element.tag = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"

    return para


def _make_table_element(cells: list[str]) -> Element:
    """Create a mock table XML element with cell texts."""
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    tbl = Element(f"{{{ns}}}tbl")
    tbl.tag = f"{{{ns}}}tbl"
    tr = SubElement(tbl, f"{{{ns}}}tr")
    for cell_text in cells:
        tc = SubElement(tr, f"{{{ns}}}tc")
        p = SubElement(tc, f"{{{ns}}}p")
        r = SubElement(p, f"{{{ns}}}r")
        t = SubElement(r, f"{{{ns}}}t")
        t.text = cell_text
    return tbl


def _make_mock_doc(
    paragraphs: list[MagicMock], extra_body_elements: list | None = None
) -> MagicMock:
    """Create a mock docx.Document."""
    doc = MagicMock()
    doc.paragraphs = paragraphs

    # Build body elements list: paragraph elements + any extras
    body_elements = [p._element for p in paragraphs]
    if extra_body_elements:
        body_elements.extend(extra_body_elements)

    doc.element = MagicMock()
    doc.element.body = body_elements
    return doc


class TestHeadingStyles:
    def test_heading_1(self, parser: DocxParser) -> None:
        h1 = _make_paragraph("Introduction", style_name="Heading 1")
        body = _make_paragraph("Body text here.")
        doc = _make_mock_doc([h1, body])

        mock_docx = MagicMock()
        mock_docx.Document.return_value = doc

        with patch.dict(sys.modules, {"docx": mock_docx}):
            sections = parser.parse(b"fake-docx", Path("doc.docx"))

        assert any(s.level == 1 and s.title == "Introduction" for s in sections)

    def test_heading_2(self, parser: DocxParser) -> None:
        h2 = _make_paragraph("Subsection", style_name="Heading 2")
        body = _make_paragraph("More text.")
        doc = _make_mock_doc([h2, body])

        mock_docx = MagicMock()
        mock_docx.Document.return_value = doc

        with patch.dict(sys.modules, {"docx": mock_docx}):
            sections = parser.parse(b"fake-docx", Path("doc.docx"))

        assert any(s.level == 2 and s.title == "Subsection" for s in sections)

    def test_heading_3(self, parser: DocxParser) -> None:
        h3 = _make_paragraph("Deep section", style_name="Heading 3")
        body = _make_paragraph("Details.")
        doc = _make_mock_doc([h3, body])

        mock_docx = MagicMock()
        mock_docx.Document.return_value = doc

        with patch.dict(sys.modules, {"docx": mock_docx}):
            sections = parser.parse(b"fake-docx", Path("doc.docx"))

        assert any(s.level == 3 and s.title == "Deep section" for s in sections)


class TestBoldFontFallback:
    def test_bold_large_detected(self, parser: DocxParser) -> None:
        # Pt(14) = 177800 EMU
        bold_para = _make_paragraph("Bold Title", bold=True, font_size=177800)
        body = _make_paragraph("Following text.")
        doc = _make_mock_doc([bold_para, body])

        mock_docx = MagicMock()
        mock_docx.Document.return_value = doc

        with patch.dict(sys.modules, {"docx": mock_docx}):
            sections = parser.parse(b"fake-docx", Path("doc.docx"))

        assert any(s.level == 1 and s.title == "Bold Title" for s in sections)

    def test_bold_small_not_heading(self, parser: DocxParser) -> None:
        # Small bold text should NOT be treated as heading
        bold_small = _make_paragraph("Just bold", bold=True, font_size=100000)
        doc = _make_mock_doc([bold_small])

        mock_docx = MagicMock()
        mock_docx.Document.return_value = doc

        with patch.dict(sys.modules, {"docx": mock_docx}):
            sections = parser.parse(b"fake-docx", Path("doc.docx"))

        # Should not have a level-1 heading
        assert not any(s.level == 1 and s.title == "Just bold" for s in sections)


class TestTablesAsText:
    def test_table_content_included(self, parser: DocxParser) -> None:
        h1 = _make_paragraph("Data Section", style_name="Heading 1")
        body = _make_paragraph("See table below.")
        tbl = _make_table_element(["Cell A", "Cell B", "Cell C"])
        doc = _make_mock_doc([h1, body], extra_body_elements=[tbl])

        mock_docx = MagicMock()
        mock_docx.Document.return_value = doc

        with patch.dict(sys.modules, {"docx": mock_docx}):
            sections = parser.parse(b"fake-docx", Path("doc.docx"))

        # Table cells should appear in content
        all_content = " ".join(s.content for s in sections)
        assert "Cell A" in all_content
        assert "Cell B" in all_content


class TestNoDocxModule:
    def test_raises_parser_error(self) -> None:
        parser = DocxParser()
        saved = sys.modules.pop("docx", None)
        try:
            with patch.dict(sys.modules, {"docx": None}):
                with pytest.raises(ParserError, match="python-docx not installed"):
                    parser.parse(b"data", Path("doc.docx"))
        finally:
            if saved is not None:
                sys.modules["docx"] = saved


class TestEmptyDocument:
    def test_empty_doc(self, parser: DocxParser) -> None:
        doc = _make_mock_doc([])

        mock_docx = MagicMock()
        mock_docx.Document.return_value = doc

        with patch.dict(sys.modules, {"docx": mock_docx}):
            sections = parser.parse(b"fake-docx", Path("doc.docx"))

        assert sections == []


class TestSupportedExtensions:
    def test_extensions(self, parser: DocxParser) -> None:
        assert parser.supported_extensions() == frozenset({".docx"})
