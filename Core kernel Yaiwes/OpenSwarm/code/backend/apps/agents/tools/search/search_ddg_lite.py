"""DuckDuckGo lite-endpoint search: the fallback when html.duckduckgo.com
serves its bot challenge (HTTP 202) or its markup drifts. lite.duckduckgo.com
is a separate frontend with simpler, stabler HTML and direct result URLs (no
uddg redirect).

Returns None on a challenge (caller decides whether that means every DDG
frontend is closed) and a formatted results string (possibly empty) on
success."""

import html
import re
from typing import List, Optional

from typeguard import typechecked

from backend.apps.agents.tools.browser_http import browser_request

P_LITE_URL = "https://lite.duckduckgo.com/lite/"
P_TIMEOUT = 12.0
P_TAG_RE = re.compile(r"<[^>]+>")
# Lite uses single-quoted class attrs today; accept either quote style so a cosmetic flip doesn't kill the parser.
P_LINK_RE = re.compile(
    r"""<a[^>]*href="([^"]+)"[^>]*class=['"]result-link['"][^>]*>(.*?)</a>""",
    flags=re.DOTALL,
)
P_SNIPPET_RE = re.compile(
    r"""<td[^>]*class=['"]result-snippet['"][^>]*>(.*?)</td>""",
    flags=re.DOTALL,
)


@typechecked
def p_strip(text: str) -> str:
    return html.unescape(P_TAG_RE.sub("", text)).strip()


@typechecked
def parse_lite_results(body: str, num_results: int) -> str:
    """Format lite's result rows; links and snippets appear in document order and pair up positionally."""
    links = P_LINK_RE.findall(body)
    snippets = [p_strip(s) for s in P_SNIPPET_RE.findall(body)]
    entries: List[str] = []
    for i, (url, raw_title) in enumerate(links[:num_results]):
        title = p_strip(raw_title)
        entry = f"[{i + 1}] {title}\n    {html.unescape(url)}"
        if i < len(snippets) and snippets[i]:
            entry += f"\n    {snippets[i]}"
        entries.append(entry)
    return "\n\n".join(entries)


@typechecked
async def search_ddg_lite(query: str, num_results: int) -> Optional[str]:
    """None = bot challenge (202), string = parsed results (may be empty on no hits)."""
    reply = await browser_request(P_LITE_URL, params={"q": query}, timeout=P_TIMEOUT)
    if reply.status == 202:
        return None
    if reply.status >= 400:
        raise RuntimeError(f"DuckDuckGo lite returned HTTP {reply.status}")
    return parse_lite_results(reply.text, num_results)
