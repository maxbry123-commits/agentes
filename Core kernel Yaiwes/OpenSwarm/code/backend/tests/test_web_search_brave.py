"""Brave rung: independent-index engine behind DuckDuckGo and Bing.

The fixture is the real markup shape captured live 2026-08-10: server-rendered
Svelte blocks keyed on data-type="web", the clean title in the title div's
`title` attribute, the real target URL on the first anchor (no redirect
wrapper), and ads carrying a different data-type."""

import pytest

import backend.apps.agents.tools.search.search_brave as BR
from backend.apps.agents.tools.browser_http import HttpReply
from backend.apps.agents.tools.search.search_brave import (
    parse_brave_results,
    search_brave,
)

P_BODY = (
    '<div id="results">'
    '<div class="snippet svelte-x" data-pos="0" data-type="ad">'
    '<a href="https://ad.example/click"><div class="title x" title="Buy Things Now">Buy Things Now</div></a></div>'
    '<div class="snippet svelte-x" data-pos="1" data-type="web" data-keynav="true">'
    '<div class="result-wrapper"><a href="https://pypi.org/project/requests/" target="_self" class="l1">'
    '<div class="site-name-content"><cite class="snippet-url">pypi.org</cite></div>'
    '<div class="title search-snippet-title line-clamp-1 svelte-y" title="requests &#183; PyPI">requests · PyPI</div></a>'
    '<div class="generic-snippet"><div class="content desktop-default-regular t-primary">'
    '<span class="t-secondary">May 14, 2026 -</span> Python HTTP for Humans. Requests is '
    "<strong>a simple, yet elegant, HTTP library</strong>.</div></div></div></div>"
    '<div class="snippet svelte-x" data-pos="2" data-type="web">'
    '<a href="https://en.wikipedia.org/wiki/Requests_(software)">'
    '<div class="title x" title="Requests (software) - Wikipedia">clipped visible text</div></a>'
    '<div class="generic-snippet"><div class="content x">Requests is an HTTP client library.</div></div></div>'
    "</div>"
)


def p_reply(status: int, text: str) -> HttpReply:
    return HttpReply(status=status, text=text, content=text.encode(),
                     content_type="text/html", url="https://search.brave.com/search")


def p_answer(monkeypatch, reply: HttpReply):
    async def p_req(url, **kw):
        return reply
    monkeypatch.setattr(BR, "browser_request", p_req)


def test_parses_title_from_attribute_url_and_snippet():
    out = parse_brave_results(P_BODY, 5)
    assert "[1] requests · PyPI" in out
    assert "https://pypi.org/project/requests/" in out
    assert "Python HTTP for Humans" in out
    assert "[2] Requests (software) - Wikipedia" in out
    assert "https://en.wikipedia.org/wiki/Requests_(software)" in out


def test_ads_are_skipped_by_data_type():
    out = parse_brave_results(P_BODY, 5)
    assert "Buy Things Now" not in out
    assert "ad.example" not in out


def test_respects_num_results():
    out = parse_brave_results(P_BODY, 1)
    assert "[1]" in out and "[2]" not in out


@pytest.mark.asyncio
async def test_http_error_reads_as_refused(monkeypatch):
    p_answer(monkeypatch, p_reply(429, "slow down"))
    assert (await search_brave("q", 5)).refused


@pytest.mark.asyncio
async def test_unrecognised_markup_is_a_refusal_not_zero_hits(monkeypatch):
    """Brave fuzzy-matches even gibberish, so an empty parse is never an honest no-hits."""
    p_answer(monkeypatch, p_reply(200, "<html><body><div>redesigned</div></body></html>"))
    assert (await search_brave("python", 5)).refused


@pytest.mark.asyncio
async def test_real_markup_answers_results(monkeypatch):
    p_answer(monkeypatch, p_reply(200, P_BODY))
    answer = await search_brave("requests", 5)
    assert not answer.refused
    assert "pypi.org" in answer.results
