"""Tests for the plain-text parser with German legal heuristics."""

from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.memory.hierarchical.models import RawSection
from cognithor.memory.hierarchical.parsers.plain_text import PlainTextParser

FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "fixtures" / "documents"


@pytest.fixture()
def parser() -> PlainTextParser:
    return PlainTextParser()


class TestGermanParagraphMarkers:
    def test_section_sign(self, parser: PlainTextParser) -> None:
        text = "\u00a7 1 Geltungsbereich\nDieser Paragraph gilt."
        sections = parser.parse(text, Path("t.txt"))
        assert any(s.level == 1 and "\u00a7 1" in s.title for s in sections)

    def test_par_dot(self, parser: PlainTextParser) -> None:
        text = "Par. 3 Lieferung\nWare wird geliefert."
        sections = parser.parse(text, Path("t.txt"))
        assert any(s.level == 1 for s in sections)


class TestAbsMarkers:
    def test_abs_detected(self, parser: PlainTextParser) -> None:
        text = "\u00a7 1 Haupt\nText.\n\nAbs. 1 Unter\nMehr Text."
        sections = parser.parse(text, Path("t.txt"))
        abs_sections = [s for s in sections if "Abs." in s.title]
        assert len(abs_sections) >= 1
        assert abs_sections[0].level == 2


class TestNumberedPatterns:
    def test_level1_numbered(self, parser: PlainTextParser) -> None:
        text = "1. Erster Punkt\nInhalt eins.\n\n2. Zweiter Punkt\nInhalt zwei."
        sections = parser.parse(text, Path("t.txt"))
        l1 = [s for s in sections if s.level == 1]
        assert len(l1) >= 2

    def test_level2_numbered(self, parser: PlainTextParser) -> None:
        text = "1. Haupt\nText.\n\n1.1 Unter\nMehr text."
        sections = parser.parse(text, Path("t.txt"))
        l2 = [s for s in sections if s.level == 2]
        assert len(l2) >= 1

    def test_level3_numbered(self, parser: PlainTextParser) -> None:
        text = "1. Haupt\nText.\n\n1.1.1 Tief verschachtelt\nDetails."
        sections = parser.parse(text, Path("t.txt"))
        l3 = [s for s in sections if s.level == 3]
        assert len(l3) >= 1


class TestAllCaps:
    def test_all_caps_heading(self, parser: PlainTextParser) -> None:
        text = "\nHAFTUNGSBESCHRAENKUNG UND SCHADENSERSATZ\n\nDie Haftung ist beschraenkt."
        sections = parser.parse(text, Path("t.txt"))
        caps = [s for s in sections if s.level == 1 and "HAFTUNG" in s.title]
        assert len(caps) >= 1

    def test_short_caps_ignored(self, parser: PlainTextParser) -> None:
        """ALL-CAPS with fewer than 3 words should not be treated as heading."""
        text = "OK DONE\nSome text follows here.\nMore text."
        sections = parser.parse(text, Path("t.txt"))
        # Should not create a level-1 heading from "OK DONE"
        caps_headings = [s for s in sections if s.level == 1 and "OK DONE" in s.title]
        assert len(caps_headings) == 0


class TestFallbackParagraphs:
    def test_no_markers_splits_by_blank_lines(self, parser: PlainTextParser) -> None:
        text = "First paragraph text.\nStill first.\n\nSecond paragraph.\n\nThird paragraph."
        sections = parser.parse(text, Path("t.txt"))
        assert len(sections) >= 2

    def test_single_paragraph(self, parser: PlainTextParser) -> None:
        text = "Just one block of text with no blank lines or markers."
        sections = parser.parse(text, Path("t.txt"))
        assert len(sections) == 1
        assert sections[0].level == 0


class TestEmpty:
    def test_empty_string(self, parser: PlainTextParser) -> None:
        sections = parser.parse("", Path("t.txt"))
        assert sections == []

    def test_whitespace_only(self, parser: PlainTextParser) -> None:
        sections = parser.parse("   \n\n  ", Path("t.txt"))
        assert sections == []


class TestFixture:
    def test_fixture_parses(self, parser: PlainTextParser) -> None:
        fixture = FIXTURE_DIR / "legal_paragraphs.txt"
        assert fixture.exists(), f"Fixture not found: {fixture}"
        text = fixture.read_text(encoding="utf-8")
        sections = parser.parse(text, fixture)
        assert len(sections) > 3
        # Should detect section sign paragraphs
        assert any("\u00a7" in s.title for s in sections)


class TestSupportedExtensions:
    def test_extensions(self, parser: PlainTextParser) -> None:
        exts = parser.supported_extensions()
        assert ".txt" in exts
        assert ".text" in exts


class TestReturnsRawSection:
    def test_types(self, parser: PlainTextParser) -> None:
        sections = parser.parse("\u00a7 1 Test\nBody.", Path("t.txt"))
        for s in sections:
            assert isinstance(s, RawSection)
