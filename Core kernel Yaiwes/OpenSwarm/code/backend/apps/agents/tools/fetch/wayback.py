"""Wayback Machine fallback for URLs the live web won't hand over.

When a page is gone (404, domain dead, article pulled) or sits behind a wall
that no client-side trick beats, the archive usually still has the REAL text,
which beats a grounded model's summary of a page it also couldn't read.

Uses `web.archive.org/web/2id_/<url>`, which redirects to the closest snapshot
and serves the ORIGINAL bytes. Without the `id_` the archive injects its own
calendar toolbar into the page, and on a Reddit snapshot that toolbar was all
the text there was: we returned "Jun JUL Aug 30 2025 2026 2027 success fail
About this capture" as if it were the article, and it cleared the substance
floor because it is made of real words. `id_` also keeps the page's own URL in
the extracted metadata instead of stamping it `hostname: archive.org`.

The documented `archive.org/wayback/available` JSON API is NOT used: it is
aggressively throttled and answered 429 on every probe from this machine, while
the redirect path answered in 0.5-3s.
"""

import re
from typing import Optional
from urllib.parse import urlparse

from typeguard import typechecked

from backend.apps.agents.tools.browser_http import browser_request
from backend.apps.agents.tools.fetch.html_to_text import html_to_text

P_WAYBACK_LATEST = "https://web.archive.org/web/2id_/"
P_ALLOWED_HOST = "web.archive.org"
P_TIMEOUT = 10.0
# Below this the "snapshot" is a stub or an archived error page, not the article.
P_MIN_SUBSTANCE_CHARS = 200
P_SNAPSHOT_RE = re.compile(r"/web/(\d{4})(\d{2})(\d{2})\d*(?:id_)?/")
# What the archive shows when the crawler was bounced to a login page: it is a 200 with real words, so only the wording gives it away.
P_INTERSTITIAL_MARKER = "response at crawl time"


@typechecked
def snapshot_date(archived_url: str) -> Optional[str]:
    """The snapshot's date, so the model knows how stale the text is."""
    match = P_SNAPSHOT_RE.search(archived_url)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


@typechecked
async def fetch_wayback(url: str) -> Optional[str]:
    """The archived page text, or None when there is no usable snapshot."""
    reply = await browser_request(P_WAYBACK_LATEST + url, timeout=P_TIMEOUT)
    # We hand the archive a caller-supplied URL, so confirm we actually ended up on the archive and not somewhere it redirected us.
    if urlparse(reply.url).hostname != P_ALLOWED_HOST:
        return None
    if reply.status != 200:
        return None
    text = html_to_text(reply.text).strip()
    if len(text) < P_MIN_SUBSTANCE_CHARS or P_INTERSTITIAL_MARKER in text:
        return None
    taken = snapshot_date(reply.url)
    header = f"Archived copy of {url}"
    header += f" (Wayback Machine snapshot from {taken}); the live page could not be read." if taken \
        else " (Wayback Machine); the live page could not be read."
    return f"{header}\n\n{text}"
