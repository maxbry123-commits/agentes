"""Bing search: the third keyless engine, straight from Microsoft's own index.

DuckDuckGo largely serves Bing's index through DuckDuckGo's frontend, so when
DDG's anti-bot wall is up the index itself is usually still reachable here.
Probed live 2026-08-10 through the Chrome-impersonating client: 200 with
server-rendered results on 3/3 queries at 0.2-0.3s, the fastest of every
engine probed.

Organic results are `<li class="b_algo">` blocks (ads live in `b_ad`, so this
match skips them by construction): title inside an `<h2><a>`, snippet in the
`b_caption` paragraph. The href is a click-tracking redirect whose `u=a1<b64>`
parameter carries the real URL base64url-encoded; a result pointing at
bing.com/ck/a would be junk to a model, so decoding it is load-bearing.

"There are no results for" is Bing's honest empty page; zero parsed blocks
without that marker means a challenge or markup drift and reads as a refusal."""

import base64
import html
import re
from typing import List

from typeguard import typechecked

from backend.apps.agents.tools.browser_http import browser_request
from backend.apps.agents.tools.search.engine_answer import EngineAnswer
from backend.apps.agents.tools.search.strip_tags import strip_tags

P_SEARCH_URL = "https://www.bing.com/search"
P_TIMEOUT = 12.0

P_BLOCK_RE = re.compile(r'<li class="b_algo.*?</li>', flags=re.DOTALL)
P_H2_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", flags=re.DOTALL)
P_HREF_RE = re.compile(r'<a[^>]*href="([^"]+)"')
P_SNIPPET_RE = re.compile(r'class="b_caption[^"]*".*?<p[^>]*>(.*?)</p>', flags=re.DOTALL)
P_REDIRECT_RE = re.compile(r"[?&]u=a1([A-Za-z0-9_\-]+)")
P_NO_RESULTS_MARKER = "There are no results for"


@typechecked
def p_real_url(raw: str) -> str:
    raw = html.unescape(raw)
    m = P_REDIRECT_RE.search(raw)
    if not m:
        return raw
    token = m.group(1)
    try:
        return base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)).decode("utf-8", "replace")
    except Exception:
        return raw


@typechecked
def parse_bing_results(body: str, num_results: int) -> str:
    """Format Bing's b_algo rows with their redirect hrefs decoded to real URLs."""
    entries: List[str] = []
    for block in P_BLOCK_RE.findall(body):
        if len(entries) >= num_results:
            break
        h2 = P_H2_RE.search(block)
        if not h2:
            continue
        href = P_HREF_RE.search(h2.group(1))
        title = strip_tags(h2.group(1))
        if not href or not title:
            continue
        entry = f"[{len(entries) + 1}] {title}\n    {p_real_url(href.group(1))}"
        snippet_match = P_SNIPPET_RE.search(block)
        if snippet_match:
            snippet = strip_tags(snippet_match.group(1))
            if snippet:
                entry += f"\n    {snippet}"
        entries.append(entry)
    return "\n\n".join(entries)


@typechecked
async def search_bing(query: str, num_results: int) -> EngineAnswer:
    """Bing's answer: results, an honest nothing, or a refusal."""
    reply = await browser_request(P_SEARCH_URL, params={"q": query}, timeout=P_TIMEOUT)
    if reply.status != 200:
        return EngineAnswer(refused=True)
    results = parse_bing_results(reply.text, num_results)
    if results:
        return EngineAnswer(results=results)
    if P_NO_RESULTS_MARKER in reply.text:
        return EngineAnswer()
    return EngineAnswer(refused=True)
