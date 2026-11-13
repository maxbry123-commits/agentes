"""A dead domain is an archive lookup, not a security refusal.

Measured: fetching a domain with no DNS records returned HTTP 400 "Refused:
DNS resolution failed", which reads like we blocked it AND short-circuited the
cascade before the Wayback tier, which exists for exactly that case. These pin
the split: unresolvable falls through, forbidden ranges still 400.
"""

import httpx
import pytest

import backend.apps.agents.tools.fetch.wayback as WB
import backend.apps.agents.tools.ssrf_guard as SG
from backend.apps.agents.tools.ssrf_guard import DomainUnreachable, SSRFBlocked, safe_fetch
from backend.apps.agents.tools.web import WebFetchTool
from backend.apps.web.web import FetchBody, fetch
from backend.tests.web_cascade_fixtures import *  # noqa: F401,F403


def p_unresolvable(monkeypatch):
    async def p_dns_dead(url):
        raise DomainUnreachable("nowhere.invalid could not be resolved (dead domain, typo, or no network)")
    monkeypatch.setattr(SG, "assert_safe_url", p_dns_dead)


def test_domain_unreachable_is_an_ssrf_blocked_subclass():
    """Every existing `except SSRFBlocked` must keep failing closed on it."""
    assert issubclass(DomainUnreachable, SSRFBlocked)


@pytest.mark.asyncio
async def test_dead_domain_reaches_the_archive(monkeypatch):
    p_unresolvable(monkeypatch)

    async def p_snapshot(url):
        return "Archived copy of the dead site\n\n" + "real archived text. " * 40
    monkeypatch.setattr(WB, "fetch_wayback", p_snapshot)

    out = await fetch(FetchBody(url="https://nowhere.invalid/page"))
    assert out["backend"] == "wayback"
    assert "real archived text" in out["content"]


@pytest.mark.asyncio
async def test_dead_domain_without_a_snapshot_says_unreachable_not_refused(monkeypatch):
    p_unresolvable(monkeypatch)
    out = await fetch(FetchBody(url="https://nowhere.invalid/page"))
    assert "Could not reach" in out["content"]
    assert "Refused" not in out["content"]


@pytest.mark.asyncio
async def test_forbidden_range_still_gets_a_hard_refusal(monkeypatch):
    from fastapi import HTTPException

    async def p_blocked(url):
        raise SSRFBlocked("URL host 169.254.169.254 is in a blocked range.")
    monkeypatch.setattr(SG, "assert_safe_url", p_blocked)

    with pytest.raises(HTTPException) as exc:
        await fetch(FetchBody(url="http://169.254.169.254/latest/meta-data/"))
    assert exc.value.status_code == 400
    assert "Refused" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_fetch_page_reports_unreachable_as_error_kind(monkeypatch):
    p_unresolvable(monkeypatch)
    page = await WebFetchTool.fetch_page("https://nowhere.invalid/page")
    assert page.kind == "error"
    assert "Could not reach" in page.text


@pytest.mark.asyncio
async def test_oversized_body_is_capped_not_buffered(monkeypatch):
    """A link to a disk image must not pull gigabytes into RAM before we truncate to 250KB."""
    served = {"bytes": 0}

    class p_HugeStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(500):
                served["bytes"] += 100_000
                yield b"x" * 100_000

        async def aclose(self) -> None:
            return None

    async def p_send(self, request, **kw):
        return httpx.Response(200, headers={"content-type": "text/plain"}, stream=p_HugeStream())
    monkeypatch.setattr(httpx.AsyncClient, "send", p_send)

    async def p_ok(url):
        return url
    monkeypatch.setattr(SG, "assert_safe_url", p_ok)

    resp = await safe_fetch("https://example.com/huge.bin", max_bytes=250_000)
    assert len(resp.content) == 250_000
    assert served["bytes"] < 50_000_000, "the stream must stop early, not download the whole file"
