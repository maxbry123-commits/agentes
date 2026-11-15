"""Startpage search: the second independent engine behind DuckDuckGo.

DuckDuckGo is one operator, so its bot challenge is one point of failure for
every keyless user. Startpage serves Google's index and answered 8/8 on the
same machine and rounds where DuckDuckGo's shipped client shape answered 4/8,
so it is a genuine second opinion rather than a retry.

It must be a POST: a GET to /sp/search is answered with an Anubis
proof-of-work interstitial (measured, ~10KB and zero results), while the POST
returns the real result page. Parsing is anchored on `result-link` /
`gl-title-link` and the `description` paragraph, never on the emotion CSS
hashes in the same class attributes, which change build to build.

Answers an `EngineAnswer` rather than a string because "closed" and
"genuinely no hits" look identical on the wire and the caller has to act on
them differently. Startpage names the honest-empty case itself, in an
"Uh-oh, there are no results for this search" page."""

import html
import re
from typing import List

from typeguard import typechecked

from backend.apps.agents.tools.browser_http import browser_request
from backend.apps.agents.tools.search.engine_answer import EngineAnswer
from backend.apps.agents.tools.search.strip_tags import strip_tags

P_SEARCH_URL = "https://www.startpage.com/sp/search"
P_TIMEOUT = 12.0

P_ANCHOR_RE = re.compile(
    r"<a\b([^>]*(?:result-link|gl-title-link)[^>]*)>(.*?)</a>", flags=re.DOTALL,
)
P_HREF_RE = re.compile(r'href="([^"]+)"')
P_TITLE_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", flags=re.DOTALL)
P_DESC_RE = re.compile(
    r'<p[^>]*class="[^"]*\bdescription\b[^"]*"[^>]*>(.*?)</p>', flags=re.DOTALL,
)
P_NO_RESULTS_MARKER = "there are no results for this search"


@typechecked
def parse_startpage_results(body: str, num_results: int) -> str:
    """Format Startpage's result rows; a snippet is only paired when it sits INSIDE its own result block."""
    anchors = list(P_ANCHOR_RE.finditer(body))
    entries: List[str] = []
    for i, match in enumerate(anchors[:num_results]):
        href = P_HREF_RE.search(match.group(1))
        if not href:
            continue
        title_match = P_TITLE_RE.search(match.group(2))
        title = strip_tags(title_match.group(1)) if title_match else strip_tags(match.group(2))
        if not title:
            continue
        entry = f"[{len(entries) + 1}] {title}\n    {html.unescape(href.group(1))}"
        block_end = anchors[i + 1].start() if i + 1 < len(anchors) else len(body)
        desc = P_DESC_RE.search(body, match.end(), block_end)
        if desc:
            snippet = strip_tags(desc.group(1))
            if snippet:
                entry += f"\n    {snippet}"
        entries.append(entry)
    return "\n\n".join(entries)


@typechecked
async def search_startpage(query: str, num_results: int) -> EngineAnswer:
    """Startpage's answer: results, an honest nothing, or a refusal."""
    reply = await browser_request(
        P_SEARCH_URL, method="POST", params={"query": query, "cat": "web"}, timeout=P_TIMEOUT,
    )
    if reply.status != 200:
        return EngineAnswer(refused=True)
    results = parse_startpage_results(reply.text, num_results)
    if results:
        return EngineAnswer(results=results)
    # Since ~2026-08 the POST gets the same ~10KB proof-of-work interstitial as GET (measured: 10,349 bytes, zero result anchors, 'challenge' markers); name it a refusal so the breaker benches the engine instead of treating the wall as a mystery empty page.
    if "challenge" in reply.text and len(reply.text) < 40_000:
        return EngineAnswer(refused=True)
    # Measured once in 14 tight-loop requests: Startpage serves its own no-results page for a query that answered 10 results a second later, so an empty page is only trustworthy when it says so.
    if P_NO_RESULTS_MARKER in reply.text:
        return EngineAnswer()
    return EngineAnswer(refused=True)
