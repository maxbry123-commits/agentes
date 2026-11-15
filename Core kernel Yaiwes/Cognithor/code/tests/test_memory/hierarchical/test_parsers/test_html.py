"""Tests for the HTML parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.memory.hierarchical.models import RawSection
from cognithor.memory.hierarchical.parsers.html import HtmlParser


@pytest.fixture()
def parser() -> HtmlParser:
    return HtmlParser()


class TestHeadingTags:
    def test_h1(self, parser: HtmlParser) -> None:
        html = "<html><body><h1>Title</h1><p>Body text.</p></body></html>"
        sections = parser.parse(html, Path("t.html"))
        assert any(s.level == 1 and s.title == "Title" for s in sections)

    def test_h2(self, parser: HtmlParser) -> None:
        html = "<h2>Subtitle</h2><p>Content.</p>"
        sections = parser.parse(html, Path("t.html"))
        assert any(s.level == 2 and s.title == "Subtitle" for s in sections)

    def test_h1_through_h6(self, parser: HtmlParser) -> None:
        html = "".join(f"<h{i}>Heading {i}</h{i}><p>Content {i}.</p>" for i in range(1, 7))
        sections = parser.parse(html, Path("t.html"))
        for level in range(1, 7):
            assert any(s.level == level and s.title == f"Heading {level}" for s in sections), (
                f"Missing heading level {level}"
            )


class TestNavFooterFiltered:
    def test_nav_removed(self, parser: HtmlParser) -> None:
        html = "<nav><a>Home</a><a>About</a></nav><h1>Title</h1><p>Body.</p>"
        sections = parser.parse(html, Path("t.html"))
        all_content = " ".join(s.content + " " + s.title for s in sections)
        assert "Home" not in all_content

    def test_footer_removed(self, parser: HtmlParser) -> None:
        html = "<h1>Title</h1><p>Body.</p><footer>Copyright 2026</footer>"
        sections = parser.parse(html, Path("t.html"))
        all_content = " ".join(s.content for s in sections)
        assert "Copyright" not in all_content

    def test_aside_removed(self, parser: HtmlParser) -> None:
        html = "<h1>Title</h1><aside>Side info</aside><p>Main content.</p>"
        sections = parser.parse(html, Path("t.html"))
        all_content = " ".join(s.content for s in sections)
        assert "Side info" not in all_content


class TestClassFiltering:
    def test_sidebar_class_removed(self, parser: HtmlParser) -> None:
        html = '<h1>Title</h1><div class="sidebar">Sidebar content</div><p>Main.</p>'
        sections = parser.parse(html, Path("t.html"))
        all_content = " ".join(s.content for s in sections)
        assert "Sidebar content" not in all_content

    def test_nav_class_removed(self, parser: HtmlParser) -> None:
        html = '<h1>Title</h1><ul class="main-nav"><li>Link</li></ul><p>Body.</p>'
        sections = parser.parse(html, Path("t.html"))
        all_content = " ".join(s.content for s in sections)
        assert "Link" not in all_content


class TestScriptStyleStripped:
    def test_script_removed(self, parser: HtmlParser) -> None:
        html = "<h1>Title</h1><script>alert('xss')</script><p>Safe content.</p>"
        sections = parser.parse(html, Path("t.html"))
        all_content = " ".join(s.content for s in sections)
        assert "alert" not in all_content

    def test_style_removed(self, parser: HtmlParser) -> None:
        html = "<h1>Title</h1><style>body{color:red}</style><p>Visible.</p>"
        sections = parser.parse(html, Path("t.html"))
        all_content = " ".join(s.content for s in sections)
        assert "color:red" not in all_content


class TestNestedSections:
    def test_nested_divs(self, parser: HtmlParser) -> None:
        html = """
        <div>
            <h1>Outer</h1>
            <div>
                <h2>Inner</h2>
                <p>Nested content.</p>
            </div>
        </div>
        """
        sections = parser.parse(html, Path("t.html"))
        assert any(s.level == 1 and s.title == "Outer" for s in sections)
        assert any(s.level == 2 and s.title == "Inner" for s in sections)


class TestEmptyHtml:
    def test_empty_string(self, parser: HtmlParser) -> None:
        sections = parser.parse("", Path("t.html"))
        assert sections == []

    def test_whitespace_only(self, parser: HtmlParser) -> None:
        sections = parser.parse("   \n  ", Path("t.html"))
        assert sections == []

    def test_empty_body(self, parser: HtmlParser) -> None:
        sections = parser.parse("<html><body></body></html>", Path("t.html"))
        assert sections == []


class TestMalformedHtml:
    def test_unclosed_tags(self, parser: HtmlParser) -> None:
        html = "<h1>Title<p>Body without closing tags"
        sections = parser.parse(html, Path("t.html"))
        # Should not crash, should produce some sections
        assert isinstance(sections, list)

    def test_mismatched_tags(self, parser: HtmlParser) -> None:
        html = "<h1>Title</h2><p>Content</div>"
        sections = parser.parse(html, Path("t.html"))
        assert isinstance(sections, list)


class TestSupportedExtensions:
    def test_extensions(self, parser: HtmlParser) -> None:
        exts = parser.supported_extensions()
        assert ".html" in exts
        assert ".htm" in exts


class TestReturnType:
    def test_returns_raw_sections(self, parser: HtmlParser) -> None:
        html = "<h1>Title</h1><p>Body.</p>"
        sections = parser.parse(html, Path("t.html"))
        for s in sections:
            assert isinstance(s, RawSection)
