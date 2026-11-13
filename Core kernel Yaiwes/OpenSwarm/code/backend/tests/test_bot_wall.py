"""A 200 that is a bot wall must not end the fetch cascade.

Any 4xx already falls through. The gap was the wall that answers 200 with
enough prose to clear the thin-page floor, which stopped the cascade one tier
before the offscreen Chromium that can actually read the page.
"""

import pytest

import backend.apps.web.web as W
from backend.apps.agents.tools.fetch.bot_wall import MAX_WALL_CHARS, looks_like_bot_wall
from backend.apps.agents.tools.fetch.page_text import PageText
from backend.apps.agents.tools.web import WebFetchTool
from backend.apps.web.web import FetchBody, fetch
from backend.tests.web_cascade_fixtures import *  # noqa: F401,F403
from backend.tests.web_cascade_fixtures import patch_browser_bridge

P_CLOUDFLARE = (
    "Just a moment...\nwww.example.com needs to review the security of your connection "
    "before proceeding.\nEnable JavaScript and cookies to continue\n" + "spacer text. " * 30
)
P_REDDIT = "Reddit - Please wait for verification\n" + "checking. " * 40


@pytest.mark.parametrize("text", [P_CLOUDFLARE, P_REDDIT])
def test_challenge_screens_are_recognised(text):
    assert looks_like_bot_wall(text)


def test_a_long_article_mentioning_the_phrase_is_not_a_wall():
    """A story about Cloudflare outages must not be thrown away for quoting the interstitial."""
    article = ("Cloudflare's interstitial, the one that says Just a moment... while it runs its "
               "checks, was at the centre of today's outage. " + "Reporting continues. " * 200)
    assert len(article) > MAX_WALL_CHARS
    assert not looks_like_bot_wall(article)


def test_ordinary_page_text_is_not_a_wall():
    assert not looks_like_bot_wall("Coroutines and tasks. This section outlines asyncio APIs.")


def p_local_returns(monkeypatch, text: str, kind: str = "html"):
    async def p_page(url, prompt=None):
        return PageText(text=f"Contents of {url}:\n\n{text}", kind=kind)
    monkeypatch.setattr(WebFetchTool, "fetch_page", staticmethod(p_page))


@pytest.mark.asyncio
async def test_bot_wall_hands_the_page_to_the_browser_tier(monkeypatch):
    p_local_returns(monkeypatch, P_CLOUDFLARE)
    patch_browser_bridge(monkeypatch, {"text": "The real rendered article body."})
    out = await fetch(FetchBody(url="https://walled.example/article"))
    assert out["backend"] == "browser"
    assert "real rendered article body" in out["content"]


@pytest.mark.asyncio
async def test_a_real_page_never_reaches_the_browser_tier(monkeypatch):
    """The browser tier costs a window and seconds; a page we already read must not pay for it."""
    p_local_returns(monkeypatch, "The genuine article body. " * 40)
    calls = []

    async def p_bridge(action, params):
        calls.append(action)
        return {"text": "should never be used"}
    monkeypatch.setattr(W, "p_browser_bridge", p_bridge)

    out = await fetch(FetchBody(url="https://fine.example/article"))
    assert out["backend"] == "local"
    assert calls == []


@pytest.mark.asyncio
async def test_browser_tier_is_tried_before_the_archive(monkeypatch):
    """The live page in our own browser beats an archived copy of it."""
    import backend.apps.agents.tools.fetch.wayback as WB
    p_local_returns(monkeypatch, P_REDDIT)
    patch_browser_bridge(monkeypatch, {"text": "Live rendered thread."})

    async def p_snapshot(url):
        raise AssertionError("the archive must not be consulted while the browser tier can serve")
    monkeypatch.setattr(WB, "fetch_wayback", p_snapshot)

    out = await fetch(FetchBody(url="https://www.reddit.com/r/programming/"))
    assert out["backend"] == "browser"


@pytest.mark.asyncio
async def test_headless_backend_skips_the_browser_tier_without_erroring(monkeypatch):
    """`bash backend/run.sh` has no Electron main bridge, so the tier must be a no-op, not a failure."""
    import backend.apps.agents.tools.fetch.wayback as WB
    p_local_returns(monkeypatch, P_REDDIT)
    patch_browser_bridge(monkeypatch, None)

    async def p_snapshot(url):
        return "Archived copy\n\n" + "archived thread text. " * 30
    monkeypatch.setattr(WB, "fetch_wayback", p_snapshot)

    out = await fetch(FetchBody(url="https://www.reddit.com/r/programming/"))
    assert out["backend"] == "wayback"


P_PERIMETERX = "Press & Hold to confirm you are\na human (and not a bot).\nReference ID eb3f614f"
P_CF_BLOCK = ("Sorry, you have been blocked\nYou are unable to access crunchbase.com\n"
              "Why have I been blocked?\n" + "boilerplate. " * 20)


@pytest.mark.parametrize("text", [P_PERIMETERX, P_CF_BLOCK])
def test_line_wrapped_challenges_are_recognised(text):
    """A rendered wall arrives wrapped ('confirm you are\\na human'), so matching must flatten it."""
    assert looks_like_bot_wall(text)


@pytest.mark.asyncio
async def test_a_walled_browser_result_falls_through_to_the_archive(monkeypatch):
    """Measured live: Cloudflare and PerimeterX beat even our real Chromium on some sites, and
    Zillow's archived copy had 6,888 characters where the live challenge screen had 106."""
    import backend.apps.agents.tools.fetch.wayback as WB
    p_local_returns(monkeypatch, "HTTP error 403 fetching it", kind="error")
    patch_browser_bridge(monkeypatch, {"text": P_PERIMETERX})

    async def p_snapshot(url):
        return "Archived copy\n\n" + "real archived listings. " * 30
    monkeypatch.setattr(WB, "fetch_wayback", p_snapshot)

    out = await fetch(FetchBody(url="https://www.zillow.com/homes/for_sale/"))
    assert out["backend"] == "wayback"
    assert "real archived listings" in out["content"]


@pytest.mark.asyncio
async def test_a_genuine_browser_render_is_kept(monkeypatch):
    p_local_returns(monkeypatch, "tiny", kind="html")
    patch_browser_bridge(monkeypatch, {"text": "nasa\n104M followers\n" + "real profile content. " * 30})
    out = await fetch(FetchBody(url="https://www.instagram.com/nasa/"))
    assert out["backend"] == "browser"
    assert "real profile content" in out["content"]
