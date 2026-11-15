"""Bing rung: Microsoft's index direct, with the click-tracker redirect decoded.

The fixture mirrors the real markup captured live 2026-08-10: b_algo list
items, the title inside an h2 anchor whose href is a bing.com/ck/a redirect
carrying the real URL base64url-encoded in `u=a1...`, the snippet in the
b_caption paragraph, and ads living in b_ad blocks."""

import base64

import pytest

import backend.apps.agents.tools.search.search_bing as BI
from backend.apps.agents.tools.browser_http import HttpReply
from backend.apps.agents.tools.search.search_bing import (
    parse_bing_results,
    search_bing,
)


def p_b64u(url: str) -> str:
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


P_BODY = (
    '<ol id="b_results">'
    '<li class="b_ad"><h2><a href="https://www.bing.com/aclick?ad=1">Sponsored Thing</a></h2></li>'
    '<li class="b_algo" data-id iid=SERP.1><h2><a target="_blank" '
    f'href="https://www.bing.com/ck/a?!&amp;&amp;p=xx&amp;u=a1{p_b64u("https://docs.python-requests.org/en/latest/")}&amp;ntb=1" '
    'h="ID=SERP,1.1">Requests: <strong>HTTP for Humans</strong></a></h2>'
    '<div class="b_caption hasdl"><p class="b_lineclamp2">Requests is an elegant and simple '
    "<strong>HTTP</strong> library for Python.</p></div></li>"
    '<li class="b_algo"><h2><a href="https://pypi.org/project/requests/">requests · PyPI</a></h2></li>'
    "</ol>"
)


def p_reply(status: int, text: str) -> HttpReply:
    return HttpReply(status=status, text=text, content=text.encode(),
                     content_type="text/html", url="https://www.bing.com/search")


def p_answer(monkeypatch, reply: HttpReply):
    async def p_req(url, **kw):
        return reply
    monkeypatch.setattr(BI, "browser_request", p_req)


def test_redirect_href_is_decoded_to_the_real_url():
    out = parse_bing_results(P_BODY, 5)
    assert "https://docs.python-requests.org/en/latest/" in out
    assert "bing.com/ck/a" not in out


def test_parses_title_snippet_and_direct_hrefs():
    out = parse_bing_results(P_BODY, 5)
    assert "[1] Requests: HTTP for Humans" in out
    assert "Requests is an elegant and simple HTTP library for Python." in out
    assert "[2] requests · PyPI" in out
    assert "https://pypi.org/project/requests/" in out


def test_ads_are_skipped_by_block_class():
    out = parse_bing_results(P_BODY, 5)
    assert "Sponsored Thing" not in out


def test_respects_num_results():
    out = parse_bing_results(P_BODY, 1)
    assert "[1]" in out and "[2]" not in out


@pytest.mark.asyncio
async def test_http_error_reads_as_refused(monkeypatch):
    p_answer(monkeypatch, p_reply(403, "nope"))
    assert (await search_bing("q", 5)).refused


@pytest.mark.asyncio
async def test_bings_own_no_results_page_is_an_answer_not_a_refusal(monkeypatch):
    p_answer(monkeypatch, p_reply(200, "<html><body>There are no results for <b>zxqv</b>.</body></html>"))
    answer = await search_bing("zxqv", 5)
    assert not answer.refused
    assert answer.results == ""


@pytest.mark.asyncio
async def test_unrecognised_markup_is_a_refusal_not_zero_hits(monkeypatch):
    p_answer(monkeypatch, p_reply(200, "<html><body><div>redesigned</div></body></html>"))
    assert (await search_bing("python", 5)).refused


@pytest.mark.asyncio
async def test_real_markup_answers_results(monkeypatch):
    p_answer(monkeypatch, p_reply(200, P_BODY))
    answer = await search_bing("requests", 5)
    assert not answer.refused
    assert "docs.python-requests.org" in answer.results
