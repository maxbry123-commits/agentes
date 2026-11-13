"""Startpage rung: the second independent engine behind DuckDuckGo.

The fixture is the real markup shape captured live 2026-07-30: an inline
<style> block INSIDE each result anchor, the title in an <h2>, volatile
emotion CSS hashes in every class attribute, and a stray description
paragraph that does not belong to any result block.
"""

import pytest

import backend.apps.agents.tools.search.search_startpage as SP
from backend.apps.agents.tools.browser_http import HttpReply
from backend.apps.agents.tools.search.search_startpage import (
    parse_startpage_results,
    search_startpage,
)

P_BODY = """
<div class="w-gl__result">
<style data-emotion="css 1bggj8v">.css-1bggj8v{color:#2E39B3;}</style>
<a class="result-title result-link css-1bggj8v" href="https://docs.python.org/3/library/asyncio.html"
   rel="noopener nofollow" data-testid="gl-title-link">
  <style data-emotion="css i3irj7">.css-i3irj7{font-size:18px;}</style>
  <h2 class="wgl-title css-i3irj7">asyncio &mdash; Asynchronous I/O</h2>
</a>
<p class="description css-1507v2l">The <b>asyncio</b> library, explained.</p>
</div>
<div class="w-gl__result">
<a class="result-title result-link css-zzz" href="https://realpython.com/async-io-python/"
   data-testid="gl-title-link"><h2 class="wgl-title css-qqq">Real Python walkthrough</h2></a>
<p class="description css-x">A hands-on tour.</p>
</div>
<p class="description css-orphan">Unrelated footer blurb, belongs to no result.</p>
"""

P_CHALLENGE_BODY = """
<html><head><script id="anubis_challenge" type="application/json">{"difficulty":2}</script></head>
<body><div class="sp-wrap">Making sure you are not a bot...</div></body></html>
"""


def p_reply(status: int, text: str) -> HttpReply:
    return HttpReply(status=status, text=text, content=text.encode(),
                     content_type="text/html", url="https://www.startpage.com/sp/search")


def p_answer(monkeypatch, reply: HttpReply, seen=None):
    async def p_req(url, **kw):
        if seen is not None:
            seen.append((url, kw.get("method"), kw.get("params")))
        return reply
    monkeypatch.setattr(SP, "browser_request", p_req)


def test_parses_title_url_and_the_snippet_from_its_own_block():
    out = parse_startpage_results(P_BODY, 5)
    assert "[1] asyncio — Asynchronous I/O" in out
    assert "https://docs.python.org/3/library/asyncio.html" in out
    assert "The asyncio library, explained." in out
    assert "[2] Real Python walkthrough" in out
    assert "A hands-on tour." in out


def test_inline_style_never_becomes_the_title():
    """Tag-stripping alone would emit the anchor's own CSS as the result title."""
    out = parse_startpage_results(P_BODY, 5)
    assert "css-" not in out
    assert "font-size" not in out


def test_an_orphan_snippet_is_not_attached_to_a_result():
    out = parse_startpage_results(P_BODY, 5)
    assert "Unrelated footer blurb" not in out


def test_respects_num_results():
    out = parse_startpage_results(P_BODY, 1)
    assert "[1]" in out and "[2]" not in out


@pytest.mark.asyncio
async def test_challenge_page_reads_as_refused_not_as_zero_hits(monkeypatch):
    # Startpage answers its proof-of-work interstitial with a normal 200, so "parsed nothing" is the only honest signal.
    p_answer(monkeypatch, p_reply(200, P_CHALLENGE_BODY))
    answer = await search_startpage("q", 5)
    assert answer.refused and not answer.results


@pytest.mark.asyncio
async def test_http_error_reads_as_refused(monkeypatch):
    p_answer(monkeypatch, p_reply(503, "nope"))
    assert (await search_startpage("q", 5)).refused


@pytest.mark.asyncio
async def test_must_post_or_startpage_serves_the_proof_of_work_wall(monkeypatch):
    seen = []
    p_answer(monkeypatch, p_reply(200, P_BODY), seen)
    out = (await search_startpage("some query", 5)).results
    assert out
    url, method, params = seen[0]
    assert url == "https://www.startpage.com/sp/search"
    assert method == "POST"
    assert params == {"query": "some query", "cat": "web"}


P_NO_RESULTS_BODY = """
<html><body><div><img src="https://cdn.startpage.com/sp/cdn/images/dislike-face.svg"/></div>
<h2>Uh-oh, there are no results for this search.</h2>
<p>Let&#x27;s see, it could be due to:</p></body></html>
"""


@pytest.mark.asyncio
async def test_startpages_own_no_results_page_is_an_answer_not_a_refusal(monkeypatch):
    """Nonsense queries must read as 'nothing matched', not as an engine that shut us out."""
    p_answer(monkeypatch, p_reply(200, P_NO_RESULTS_BODY))
    answer = await search_startpage("zxqvbnmklwertyuiopasdfg", 5)
    assert not answer.refused
    assert answer.results == ""


@pytest.mark.asyncio
async def test_unrecognised_markup_is_a_refusal_not_zero_hits(monkeypatch):
    """If Startpage redesigns, we must fail loudly rather than report the web as empty."""
    p_answer(monkeypatch, p_reply(200, "<html><body><div class=whatever>redesigned</div></body></html>"))
    assert (await search_startpage("python", 5)).refused
