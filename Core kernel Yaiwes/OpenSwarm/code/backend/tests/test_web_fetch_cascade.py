"""Deadline-bounded /api/web/fetch cascade.

Mirrors /search: the local httpx + trafilatura read is the fast path, the
packaged browser and the Wayback archive cover JS walls and dead links, and the
grounded fetchers are the last resort. A body with no text layer at all stops
the chain rather than buying a paid summary of nothing.
"""

import time

import pytest

import backend.apps.agents.tools.fetch.wayback as WB
import backend.apps.web.web as W
from backend.apps.agents.tools.fetch.page_text import PageText
from backend.apps.agents.tools.web import WebFetchTool
from backend.apps.web.web import fetch, FetchBody
from backend.tests.web_cascade_fixtures import (  # noqa: F401
    allow_urls,
    patch_browser_bridge,
    no_network,
)


def p_local_returns(monkeypatch, text, kind="html"):
    async def p_fetch(url, prompt=None):
        return PageText(text=text, kind=kind)
    monkeypatch.setattr(WebFetchTool, "fetch_page", staticmethod(p_fetch))



@pytest.mark.asyncio
async def test_fetch_local_first_wins_and_is_fast(monkeypatch):
    big = "Contents of https://x.example:\n\n" + ("real article body " * 50)
    p_local_returns(monkeypatch, big)
    async def p_boom(*a, **k):
        raise AssertionError("grounded fetch should not run when local has content")
    monkeypatch.setattr(W, "gemini_grounded_call", p_boom)

    t = time.monotonic()
    res = await fetch(FetchBody(url="https://x.example"))
    assert res["backend"] == "local"
    assert "real article body" in res["content"]
    assert time.monotonic() - t < 1.0


@pytest.mark.asyncio
async def test_fetch_thin_local_falls_to_grounded(monkeypatch):
    p_local_returns(monkeypatch, "Contents of https://spa.example:\n\n")  # JS wall, empty body
    monkeypatch.setattr(W, "resolve_gemini_api_key", lambda: "gkey")
    async def p_gem(api_key, prompt, *, use_url_context):
        return {"text": "rendered page text from grounding", "chunks": []}
    monkeypatch.setattr(W, "gemini_grounded_call", p_gem)

    res = await fetch(FetchBody(url="https://spa.example"))
    assert res["backend"] == "gemini_native"
    assert "rendered page text" in res["content"]


@pytest.mark.asyncio
async def test_fetch_local_error_returned_as_last_resort(monkeypatch):
    p_local_returns(monkeypatch, "HTTP error 403 fetching https://blocked.example", kind="error")
    # no grounded keys/subs (autouse fixtures) -> all grounded skip/fail
    res = await fetch(FetchBody(url="https://blocked.example"))
    assert res["backend"] == "local"
    assert "HTTP error 403" in res["content"]


@pytest.mark.asyncio
async def test_fetch_falls_to_the_archive_when_the_live_page_is_gone(monkeypatch):
    """A dead link is exactly what the archive is for; the real text beats a grounded summary of nothing."""
    p_local_returns(monkeypatch, "HTTP error 404 fetching https://gone.example/post")

    async def p_snapshot(url):
        return "Archived copy of https://gone.example/post (Wayback Machine snapshot from 2026-05-08)\n\nThe original text."
    monkeypatch.setattr(WB, "fetch_wayback", p_snapshot)

    async def p_boom(*a, **k):
        raise AssertionError("a paid fetcher must not run once the archive answered")
    monkeypatch.setattr(W, "gemini_grounded_call", p_boom)

    res = await fetch(FetchBody(url="https://gone.example/post"))
    assert res["backend"] == "wayback"
    assert "The original text." in res["content"]


@pytest.mark.asyncio
async def test_browser_fetch_tier_fires_when_local_thin(monkeypatch):
    p_local_returns(monkeypatch, "Contents of x:\n\ntiny")  # <200 chars -> try_local returns None
    patch_browser_bridge(monkeypatch, {"title": "T", "text": "the full rendered article body " * 20, "url": "https://x.example"})

    res = await fetch(FetchBody(url="https://x.example"))
    assert res["backend"] == "browser"
    assert "rendered article" in res["content"]


@pytest.mark.asyncio
async def test_an_unreadable_binary_stops_the_cascade_instead_of_buying_a_summary(monkeypatch):
    """A PNG has no text for ANY tier to find; spending a paid fetcher on it buys nothing."""
    p_local_returns(monkeypatch, "This URL is not a readable document: image/png, 219 KB of binary data.",
                    kind="binary")
    monkeypatch.setattr(W, "resolve_gemini_api_key", lambda: "gkey")

    async def p_boom(*a, **k):
        raise AssertionError("a paid fetcher must never be spent on a body with no text layer")
    monkeypatch.setattr(W, "gemini_grounded_call", p_boom)

    res = await fetch(FetchBody(url="https://x.example/photo.png"))
    assert res["backend"] == "local"
    assert "image/png" in res["content"]


@pytest.mark.asyncio
async def test_a_scanned_pdf_also_stops_the_cascade(monkeypatch):
    p_local_returns(monkeypatch, "This URL is a PDF (4 MB) with no extractable text layer.",
                    kind="pdf_unreadable")
    monkeypatch.setattr(W, "resolve_gemini_api_key", lambda: "gkey")

    async def p_boom(*a, **k):
        raise AssertionError("a scanned PDF is not worth a paid fetcher either")
    monkeypatch.setattr(W, "gemini_grounded_call", p_boom)

    res = await fetch(FetchBody(url="https://x.example/scan.pdf"))
    assert res["backend"] == "local"
