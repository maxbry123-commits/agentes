"""The keyless rungs go out through ONE browser-shaped client.

Why it matters: DuckDuckGo's 202 challenge keys on the client's TLS
fingerprint, not on headers or verb. Measured over 8 interleaved randomised
rounds, plain httpx scored 4/8 and Chrome impersonation 8/8 on the same
queries. These pin the seam and the degrade path.
"""

import pytest

import backend.apps.agents.tools.browser_http as BH
import backend.apps.agents.tools.search.search_ddg as SD
import backend.apps.agents.tools.search.search_ddg_lite as SDL
from backend.apps.agents.tools.browser_http import BROWSER_HEADERS, HttpReply, browser_request


def p_reply(status=200, text="ok"):
    return HttpReply(status=status, text=text, content=text.encode(),
                     content_type="text/html", url="https://x.example")


def p_record_transports(monkeypatch):
    used = []

    async def p_imp(*a, **k):
        used.append("impersonated")
        return p_reply()

    async def p_pl(*a, **k):
        used.append("plain")
        return p_reply()

    monkeypatch.setattr(BH, "p_impersonated", p_imp)
    monkeypatch.setattr(BH, "p_plain", p_pl)
    return used


@pytest.mark.asyncio
async def test_impersonates_when_the_client_is_installed(monkeypatch):
    used = p_record_transports(monkeypatch)
    monkeypatch.setattr(BH, "impersonation_available", lambda: True)
    await browser_request("https://x.example")
    assert used == ["impersonated"]


@pytest.mark.asyncio
async def test_degrades_to_httpx_instead_of_failing(monkeypatch):
    """A missing wheel must cost us reliability, never the whole backend."""
    used = p_record_transports(monkeypatch)
    monkeypatch.setattr(BH, "impersonation_available", lambda: False)
    reply = await browser_request("https://x.example")
    assert used == ["plain"]
    assert reply.status == 200


@pytest.mark.asyncio
async def test_caller_headers_win_over_the_defaults(monkeypatch):
    seen = {}

    async def p_pl(url, method, params, headers, timeout, follow_redirects):
        seen.update(headers)
        return p_reply()

    monkeypatch.setattr(BH, "p_plain", p_pl)
    monkeypatch.setattr(BH, "impersonation_available", lambda: False)
    await browser_request("https://x.example", headers={"Accept-Language": "de-DE"})
    assert seen["Accept-Language"] == "de-DE"
    assert seen["User-Agent"] == BROWSER_HEADERS["User-Agent"]


def test_default_headers_look_like_a_real_navigation():
    # A bare User-Agent is the tell that gets a scraper challenged.
    for key in ("User-Agent", "Accept", "Accept-Language", "Sec-Fetch-Mode", "Upgrade-Insecure-Requests"):
        assert BROWSER_HEADERS.get(key)
    assert "Chrome/" in BROWSER_HEADERS["User-Agent"]


@pytest.mark.asyncio
async def test_ddg_rungs_send_the_query_as_a_get_param(monkeypatch):
    """Pins the shape: a GET with params, through the shared seam, on both frontends."""
    calls = []

    async def p_req(url, **kw):
        calls.append((url, kw.get("method", "GET"), kw.get("params")))
        return p_reply(202, "challenge")

    monkeypatch.setattr(SD, "browser_request", p_req)
    monkeypatch.setattr(SDL, "browser_request", p_req)
    from backend.apps.agents.tools.web import DDGRateLimited
    with pytest.raises(DDGRateLimited):
        await SD.search_ddg("some query", 5)

    assert [c[0] for c in calls] == [
        "https://html.duckduckgo.com/html/",
        "https://lite.duckduckgo.com/lite/",
    ]
    for _, method, params in calls:
        assert method == "GET"
        assert params == {"q": "some query"}


def test_curl_cffi_is_a_declared_dependency():
    """It must be in BOTH files: the packaged python-env installs from the LOCK."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert "curl_cffi==" in (root / "requirements.txt").read_text()
    assert "curl-cffi==" in (root / "requirements.lock").read_text()
