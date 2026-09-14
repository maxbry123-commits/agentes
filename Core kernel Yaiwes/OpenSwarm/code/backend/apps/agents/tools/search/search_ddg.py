"""DuckDuckGo web search: html endpoint primary, lite endpoint fallback.

The html endpoint is the richer parse; lite (see search_ddg_lite) covers the two
ways html dies: the 202 bot challenge and silent markup drift. Only both
endpoints challenging raises DDGRateLimited, so free search no longer has a
single point of failure (the outage class that stranded subscription-only users
on "No search backend is configured").

Both rungs go out through `browser_http`, whose Chrome TLS fingerprint is what
actually decides whether DuckDuckGo answers; a plain httpx client scored 4/8 on
the same queries this one scored 8/8 on."""

import html
import re

from backend.apps.agents.tools.browser_http import CHROME_UA
from backend.apps.agents.tools.browser_http import browser_request
from backend.apps.agents.tools.search.search_ddg_lite import search_ddg_lite

HTTP_TIMEOUT = 30
USER_AGENT = CHROME_UA


class DDGRateLimited(Exception):
    """Every DuckDuckGo frontend answered with the bot challenge (HTTP 202).

    Named for history; this is an anti-automation challenge keyed on the
    client's fingerprint, NOT a per-IP rate limit. Distinct from 'genuinely
    zero hits' so the caller can fail over to another backend instead of
    reporting an empty search to the user."""


def strip_html(raw_html: str) -> str:
    """Naive but effective HTML to plain-text conversion."""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def search_ddg(query: str, num_results: int) -> str:
    """Query DuckDuckGo's html endpoint and parse results; lite is the free fallback."""
    reply = await browser_request(
        "https://html.duckduckgo.com/html/", params={"q": query}, timeout=HTTP_TIMEOUT,
    )
    # DDG serves its bot challenge as 202 (a ~14KB no-results page), which is a 2xx so a status check sails right past it. Before giving up, try the lite frontend; only when BOTH challenge is free DDG actually dead.
    if reply.status == 202:
        lite = await search_ddg_lite(query, num_results)
        if lite is None:
            raise DDGRateLimited(query)
        return lite
    # A hard block (403 is what html escalates to after the 202s) used to skip lite entirely, so a whole second frontend went untried; measured 7 times in one 44-query round.
    if reply.status >= 400:
        try:
            lite = await search_ddg_lite(query, num_results)
        except Exception as exc:
            raise RuntimeError(f"DuckDuckGo html returned HTTP {reply.status}; lite: {exc}") from None
        if lite is None:
            raise DDGRateLimited(query)
        if lite:
            return lite
        raise RuntimeError(f"DuckDuckGo html returned HTTP {reply.status}")

    body = reply.text

    result_blocks = re.findall(
        r'<div[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</div>\s*(?=<div[^>]*class="[^"]*result|$)',
        body,
        flags=re.DOTALL,
    )

    entries: list[str] = []
    for block in result_blocks:
        if len(entries) >= num_results:
            break

        # Handle both class-before-href and href-before-class attribute orders.
        link_match = re.search(
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            block,
            flags=re.DOTALL,
        )
        if not link_match:
            link_match = re.search(
                r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>',
                block,
                flags=re.DOTALL,
            )
        if not link_match:
            continue

        raw_url = html.unescape(link_match.group(1))

        # Drop sponsored rows: DDG ads point at its own y.js click-tracker (ad_domain/ad_provider) instead of a real uddg= redirect, so they'd otherwise show up as junk "duckduckgo.com/y.js?ad_..." results.
        if "/y.js?" in raw_url or "ad_provider=" in raw_url or "ad_domain=" in raw_url:
            continue

        title = strip_html(link_match.group(2)).strip()

        snippet_match = re.search(
            r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
            block,
            flags=re.DOTALL,
        )
        snippet = strip_html(snippet_match.group(1)).strip() if snippet_match else ""

        # DDG wraps URLs in a redirect; extract the real one.
        real_url_match = re.search(r"uddg=([^&]+)", raw_url)
        if real_url_match:
            from urllib.parse import unquote
            url = unquote(real_url_match.group(1))
        else:
            url = raw_url

        entry = f"[{len(entries) + 1}] {title}\n    {url}"
        if snippet:
            entry += f"\n    {snippet}"
        entries.append(entry)

    # 200 with zero parsed entries usually means DDG changed its markup out from under the regexes (it has before), not a genuine no-hits; lite's simpler shape is the safety net.
    if not entries:
        lite = await search_ddg_lite(query, num_results)
        if lite:
            return lite
    return "\n\n".join(entries)
