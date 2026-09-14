"""The archive's redirect interstitial is not a copy of the page.

Measured on instagram.com/nasa: the Wayback tier answered 200 and we handed
the model 225 characters reading "Got an HTTP 302 response at crawl time /
Redirecting to .../accounts/login". It passed the substance floor because the
interstitial has real words in it, so only the wording gives it away.
"""

import pytest

import backend.apps.agents.tools.fetch.wayback as WB
from backend.apps.agents.tools.browser_http import HttpReply
from backend.apps.agents.tools.fetch.wayback import fetch_wayback, snapshot_date

P_ARCHIVED_URL = "https://web.archive.org/web/20260711073650/https://example.com/story"


def p_patch(monkeypatch, status: int, text: str, url: str = P_ARCHIVED_URL):
    async def p_req(u, **kw):
        return HttpReply(status=status, text=text, content=text.encode(),
                         content_type="text/html", url=url)
    monkeypatch.setattr(WB, "browser_request", p_req)


P_INTERSTITIAL = (
    "<html><body><p>Loading...</p><p>https://www.instagram.com/nasa/</p>"
    "<p>07:36:50 July 11, 2026</p><p>Got an HTTP 302 response at crawl time</p>"
    "<p>Redirecting to...</p><p>https://www.instagram.com/accounts/login/?next=%2Fnasa%2F</p>"
    "<p>Wayback Machine has not archived that URL beyond the redirect target given here.</p>"
    "</body></html>"
)

P_REAL_ARTICLE = (
    "<html><body><article><p>" + "The archived article body says something real. " * 20
    + "</p></article></body></html>"
)


@pytest.mark.asyncio
async def test_redirect_interstitial_is_not_content(monkeypatch):
    p_patch(monkeypatch, 200, P_INTERSTITIAL)
    assert await fetch_wayback("https://www.instagram.com/nasa/") is None


@pytest.mark.asyncio
async def test_real_snapshot_still_returns_with_its_date(monkeypatch):
    p_patch(monkeypatch, 200, P_REAL_ARTICLE)
    out = await fetch_wayback("https://example.com/story")
    assert out is not None
    assert "archived article body" in out
    assert "2026-07-11" in out


@pytest.mark.asyncio
async def test_stub_snapshot_below_the_floor_is_rejected(monkeypatch):
    p_patch(monkeypatch, 200, "<html><body><p>Loading...</p></body></html>")
    assert await fetch_wayback("https://example.com/story") is None


@pytest.mark.asyncio
async def test_offsite_redirect_is_refused(monkeypatch):
    """We hand the archive a caller-supplied URL, so landing anywhere else means no answer."""
    p_patch(monkeypatch, 200, P_REAL_ARTICLE, url="https://evil.example/whatever")
    assert await fetch_wayback("https://example.com/story") is None


def test_snapshot_date_parsing():
    assert snapshot_date(P_ARCHIVED_URL) == "2026-07-11"
    assert snapshot_date("https://web.archive.org/nope") is None


@pytest.mark.asyncio
async def test_raw_snapshot_form_is_requested(monkeypatch):
    """Without `id_` the archive injects its calendar toolbar, and on a Reddit snapshot
    that toolbar WAS the whole extracted text."""
    seen = []

    async def p_req(u, **kw):
        seen.append(u)
        return HttpReply(status=200, text=P_REAL_ARTICLE, content=P_REAL_ARTICLE.encode(),
                         content_type="text/html", url=P_ARCHIVED_URL)
    monkeypatch.setattr(WB, "browser_request", p_req)
    await fetch_wayback("https://example.com/story")
    assert seen == ["https://web.archive.org/web/2id_/https://example.com/story"]


def test_snapshot_date_parsing_survives_the_raw_form():
    assert snapshot_date("https://web.archive.org/web/20260727222838id_/https://x.example/") == "2026-07-27"


@pytest.mark.asyncio
async def test_archive_toolbar_text_alone_is_below_the_floor(monkeypatch):
    toolbar = ("<html><body>Jun JUL Aug 30 2025 2026 2027 success fail About this capture "
               "COLLECTED BY Collection: Save Page Now TIMESTAMPS</body></html>")
    p_patch(monkeypatch, 200, toolbar)
    assert await fetch_wayback("https://www.reddit.com/r/programming/") is None
