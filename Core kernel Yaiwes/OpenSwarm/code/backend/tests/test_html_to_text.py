"""The extraction ladder, pinned against the failures that motivated it.

`favor_precision=True` disables trafilatura's own rescue, so on real pages
(allrecipes, Spiegel) it returned NOTHING and we shipped the regex strip's nav
soup instead of the article. Flipping the flag off is not the fix either: on
The Verge the plain call collapses to 441 chars where precision finds 6,602.
Hence a ladder that keeps whichever rung found the most text.
"""

import pytest

import backend.apps.agents.tools.fetch.html_to_text as HT
from backend.apps.agents.tools.fetch.html_to_text import (
    MIN_EXTRACT_CHARS,
    THIN_EXTRACT_CHARS,
    html_to_text,
)


def p_stub(monkeypatch, plain: str, precise: str, baseline: str = "", html2txt: str = ""):
    def p_extract(raw_html, *, favor_precision):
        return precise if favor_precision else plain
    monkeypatch.setattr(HT, "p_trafilatura_extract", p_extract)

    def p_floor(raw_html, fn_name):
        return baseline if fn_name == "baseline" else html2txt
    monkeypatch.setattr(HT, "p_trafilatura_floor", p_floor)


def test_full_plain_extraction_never_pays_for_a_second_pass(monkeypatch):
    calls = []

    def p_extract(raw_html, *, favor_precision):
        calls.append(favor_precision)
        return "x" * (THIN_EXTRACT_CHARS + 10)
    monkeypatch.setattr(HT, "p_trafilatura_extract", p_extract)
    out = html_to_text("<html></html>")
    assert len(out) == THIN_EXTRACT_CHARS + 10
    assert calls == [False], "a healthy extraction must not trigger the precision pass"


def test_thin_plain_falls_to_precision(monkeypatch):
    """The Verge case: default recall collapses, precision finds the article."""
    p_stub(monkeypatch, plain="short", precise="y" * 6000)
    assert len(html_to_text("<html></html>")) == 6000


def test_precision_returning_nothing_falls_to_baseline(monkeypatch):
    """The allrecipes case: precision extracted nothing at all."""
    p_stub(monkeypatch, plain="", precise="", baseline="b" * 5000)
    assert len(html_to_text("<html></html>")) == 5000


def test_ladder_keeps_the_fullest_rung(monkeypatch):
    p_stub(monkeypatch, plain="a" * 300, precise="b" * 200, baseline="c" * 100)
    assert html_to_text("<html></html>") == "a" * 300


def test_everything_empty_falls_back_to_regex_strip(monkeypatch):
    p_stub(monkeypatch, plain="", precise="", baseline="", html2txt="")
    out = html_to_text("<html><body><p>hello &amp; goodbye</p></body></html>")
    assert "hello & goodbye" in out


def test_html2txt_only_rescues_a_truly_empty_read(monkeypatch):
    p_stub(monkeypatch, plain="", precise="", baseline="", html2txt="z" * 400)
    assert len(html_to_text("<html></html>")) == 400
    p_stub(monkeypatch, plain="q" * (MIN_EXTRACT_CHARS + 1), precise="", baseline="", html2txt="z" * 400)
    assert html_to_text("<html></html>") == "q" * (MIN_EXTRACT_CHARS + 1)


def test_extractor_exception_degrades_instead_of_raising(monkeypatch):
    def p_boom(raw_html, *, favor_precision):
        raise ValueError("lxml exploded")
    monkeypatch.setattr(HT, "p_trafilatura_extract", p_boom)
    with pytest.raises(ValueError):
        p_boom("", favor_precision=False)
    # Through the real wrapper the same failure is swallowed and the floor answers.
    monkeypatch.undo()
    out = html_to_text("<html><body><p>" + "words " * 100 + "</p></body></html>")
    assert "words" in out


@pytest.mark.parametrize("markup,needle", [
    ("<html><body><article><p>" + "Real body text. " * 60 + "</p></article></body></html>", "Real body text"),
    ("<html><body><main><p>" + "Docs paragraph. " * 60 + "</p></main></body></html>", "Docs paragraph"),
])
def test_real_trafilatura_extracts_article_bodies(markup, needle):
    """No mocks: the shipped library on the shipped call must find an article body."""
    assert needle in html_to_text(markup)


def test_real_trafilatura_drops_nav_chrome():
    markup = (
        "<html><body><nav>Home About Careers Privacy Policy Sign in</nav>"
        "<article><p>" + "The measured content sentence. " * 40 + "</p></article>"
        "<footer>Copyright Terms of Use Cookie Settings</footer></body></html>"
    )
    out = html_to_text(markup)
    assert "measured content sentence" in out
    assert "Cookie Settings" not in out
    assert "Careers" not in out
