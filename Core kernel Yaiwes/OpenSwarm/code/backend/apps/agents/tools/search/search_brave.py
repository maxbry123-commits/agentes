"""Brave search: a keyless engine with its OWN index behind DuckDuckGo.

Brave runs its own crawler, so it fails independently of the Bing-fed engines
(DuckDuckGo, Bing itself) and of Google (Startpage). Probed live 2026-08-10
through the Chrome-impersonating client: 200 with server-rendered results on
3/3 queries at 0.7-0.9s, while Mojeek, Ecosia and Yep 403'd the same client
on the same machine and Qwant served a JS shell.

The SERP is server-rendered Svelte: each organic result is a
`<div class="snippet ..." data-type="web">` block whose first anchor carries
the REAL target URL (no redirect wrapper), whose title div carries the clean
text in its `title` attribute, and whose description sits in a
`<div class="content ...">`. Ads carry a different data-type, so matching
`data-type="web"` skips them by construction.

A gibberish query still returns fuzzy matches (measured: 19 blocks plus a
"Not many great matches" banner), so zero parsed blocks on a 200 is markup
drift or a challenge page, never an honest no-hits; both read as a refusal.

Hammered with 50 back-to-back queries it answered the first 11 then throttled,
and recovered within about a minute, so it belongs BEHIND an unthrottled rung
in the race (Bing went 50/50 on the same burst) where it only sees the
occasional rescue query, not the firehose."""

import html
import re
from typing import List

from typeguard import typechecked

from backend.apps.agents.tools.browser_http import browser_request
from backend.apps.agents.tools.search.engine_answer import EngineAnswer
from backend.apps.agents.tools.search.strip_tags import strip_tags

P_SEARCH_URL = "https://search.brave.com/search"
P_TIMEOUT = 12.0

P_BLOCK_SPLIT_RE = re.compile(r'data-type="web"')
P_HREF_RE = re.compile(r'<a href="(https?://[^"]+)"')
P_TITLE_RE = re.compile(r'class="title[^"]*"[^>]*\btitle="([^"]*)"')
P_DESC_RE = re.compile(r'<div class="content[^"]*"[^>]*>(.*?)</div>', flags=re.DOTALL)


@typechecked
def parse_brave_results(body: str, num_results: int) -> str:
    """Format Brave's organic rows; each split chunk starts with one result's own markup."""
    chunks = P_BLOCK_SPLIT_RE.split(body)[1:]
    entries: List[str] = []
    for chunk in chunks:
        if len(entries) >= num_results:
            break
        href = P_HREF_RE.search(chunk)
        title = P_TITLE_RE.search(chunk)
        if not href or not title:
            continue
        title_text = html.unescape(title.group(1)).strip()
        if not title_text:
            continue
        entry = f"[{len(entries) + 1}] {title_text}\n    {html.unescape(href.group(1))}"
        desc = P_DESC_RE.search(chunk)
        if desc:
            snippet = strip_tags(desc.group(1))
            if snippet:
                entry += f"\n    {snippet}"
        entries.append(entry)
    return "\n\n".join(entries)


@typechecked
async def search_brave(query: str, num_results: int) -> EngineAnswer:
    """Brave's answer: results, or a refusal (it fuzzy-matches, so empty means blocked or drifted)."""
    reply = await browser_request(P_SEARCH_URL, params={"q": query}, timeout=P_TIMEOUT)
    if reply.status != 200:
        return EngineAnswer(refused=True)
    results = parse_brave_results(reply.text, num_results)
    if results:
        return EngineAnswer(results=results)
    return EngineAnswer(refused=True)
