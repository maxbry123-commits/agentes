"""Tests for the Markdown parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.memory.hierarchical.models import RawSection
from cognithor.memory.hierarchical.parsers.markdown import MarkdownParser

FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "fixtures" / "documents"


@pytest.fixture()
def parser() -> MarkdownParser:
    return MarkdownParser()


class TestAtxHeadings:
    def test_h1(self, parser: MarkdownParser) -> None:
        sections = parser.parse("# Title\nBody text.", Path("t.md"))
        assert any(s.level == 1 and s.title == "Title" for s in sections)

    def test_h2(self, parser: MarkdownParser) -> None:
        sections = parser.parse("## Subtitle\nMore text.", Path("t.md"))
        assert any(s.level == 2 and s.title == "Subtitle" for s in sections)

    def test_h3_through_h6(self, parser: MarkdownParser) -> None:
        md = "\n".join(f"{'#' * i} Heading {i}\nContent {i}." for i in range(3, 7))
        sections = parser.parse(md, Path("t.md"))
        for level in range(3, 7):
            assert any(s.level == level and s.title == f"Heading {level}" for s in sections), (
                f"Missing heading level {level}"
            )

    def test_trailing_hashes_stripped(self, parser: MarkdownParser) -> None:
        sections = parser.parse("## Hello ##\nBody.", Path("t.md"))
        assert any(s.title == "Hello" for s in sections)


class TestSetextHeadings:
    def test_setext_h1(self, parser: MarkdownParser) -> None:
        sections = parser.parse("Title\n=====\nBody.", Path("t.md"))
        assert any(s.level == 1 and s.title == "Title" for s in sections)

    def test_setext_h2(self, parser: MarkdownParser) -> None:
        sections = parser.parse("Subtitle\n--------\nBody.", Path("t.md"))
        assert any(s.level == 2 and s.title == "Subtitle" for s in sections)


class TestCodeBlocks:
    def test_code_blocks_atomic(self, parser: MarkdownParser) -> None:
        md = "# Section\nBefore code.\n```python\ndef hello():\n    pass\n```\nAfter code."
        sections = parser.parse(md, Path("t.md"))
        # The code block must be inside a single section, not split
        code_sections = [s for s in sections if "def hello" in s.content]
        assert len(code_sections) == 1
        assert "```python" in code_sections[0].content
        assert "```" in code_sections[0].content

    def test_heading_inside_fence_ignored(self, parser: MarkdownParser) -> None:
        md = "# Real\n```\n# Not a heading\n```\n"
        sections = parser.parse(md, Path("t.md"))
        heading_sections = [s for s in sections if s.level >= 1]
        assert len(heading_sections) == 1
        assert heading_sections[0].title == "Real"


class TestContentBetweenHeadings:
    def test_paragraphs_captured(self, parser: MarkdownParser) -> None:
        md = "# A\nParagraph one.\n\nParagraph two.\n## B\nBody B."
        sections = parser.parse(md, Path("t.md"))
        sec_a = next(s for s in sections if s.title == "A")
        assert "Paragraph one." in sec_a.content
        assert "Paragraph two." in sec_a.content

    def test_content_before_first_heading(self, parser: MarkdownParser) -> None:
        md = "Preamble text.\n# Title\nBody."
        sections = parser.parse(md, Path("t.md"))
        assert sections[0].level == 0
        assert "Preamble" in sections[0].content


class TestNoHeadings:
    def test_no_headings(self, parser: MarkdownParser) -> None:
        sections = parser.parse("Just some plain text.\nAnother line.", Path("t.md"))
        assert len(sections) == 1
        assert sections[0].level == 0
        assert sections[0].title == "Document"
        assert "Just some plain text." in sections[0].content


class TestEmptyDocument:
    def test_empty_string(self, parser: MarkdownParser) -> None:
        sections = parser.parse("", Path("t.md"))
        assert sections == []

    def test_whitespace_only(self, parser: MarkdownParser) -> None:
        sections = parser.parse("   \n\n  ", Path("t.md"))
        assert sections == []


class TestFixture:
    def test_fixture_parses(self, parser: MarkdownParser) -> None:
        fixture = FIXTURE_DIR / "avb_sample.md"
        assert fixture.exists(), f"Fixture not found: {fixture}"
        text = fixture.read_text(encoding="utf-8")
        sections = parser.parse(text, fixture)
        assert len(sections) > 3
        # Should have the main title
        assert any("Allgemeine Versicherungsbedingungen" in s.title for s in sections)


class TestSupportedExtensions:
    def test_extensions(self, parser: MarkdownParser) -> None:
        exts = parser.supported_extensions()
        assert ".md" in exts
        assert ".markdown" in exts


class TestRawSectionType:
    def test_returns_raw_sections(self, parser: MarkdownParser) -> None:
        sections = parser.parse("# H\nBody.", Path("t.md"))
        for s in sections:
            assert isinstance(s, RawSection)
