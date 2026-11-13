"""Find a site's compose URL by reading the links the site already publishes.

The compose-URL table in `compose_entry` is worth 92.9% composer reachability on the five hosts it
knows and exactly 0% everywhere else, measured live over 8 logged-in sites. Two attempts to close
that gap by making the aux navigator click better were falsified in the same session (0/8 both
times, at roughly double the wall time), so the lever is not better clicking, it is getting the URL.

The generalizable source is the page itself. A site that has a composer links to it: "Start a post",
"Ask Question", "Create", "New story". Reading those anchors is precise where guessing paths is not,
because it is the site's own navigation rather than a list of shapes we hope it matches, and it
needs no per-site knowledge. It also degrades honestly: no matching anchor means no candidate, and
the caller runs exactly as it does today.

The ranking here is deliberately pure, so the part that decides where to send someone's browser is
testable without a browser. The page-reading half is one expression; the judgement half is below it.
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from typeguard import typechecked

from backend.apps.agents.browser import compose_entry

# How many links to bring back. Enough to cover a nav bar plus a sidebar; a page with more than
# this has a hundred feed links and the composer is not going to be number 401.
MAX_LINKS = 400
# How many candidates the caller may actually navigate to. Each miss costs a real page load, and
# past two the aux loop is the cheaper remaining option.
MAX_CANDIDATES = 2
# Longest a control's label can be before it is prose rather than a button. "Start a post" is 3.
MAX_LABEL_WORDS = 4

# Path segments that mean "start something new" across platforms rather than on one host: /submit
# is reddit-shaped, /questions/ask is every StackExchange, /new-story is medium-shaped, /new/text is
# tumblr-shaped, /compose is mail and chat.
#
# A WHOLE segment, never a substring. Substring matching was tried and produced garbage on the
# first live read: "post" matched inside `/explore/top-posts` and "new" inside a permalink
# `/actuallysara/823.../new-photo-of-connor...`, so the tier proposed navigating to a random blog
# post. `post` itself is deliberately absent even as a segment, because permalinks are `/post/<id>`
# on half the web and a false candidate costs a real page load.
P_PATH_HINTS: Tuple[str, ...] = (
    "submit", "compose", "new", "create", "ask", "publish", "write", "share",
    "new-story", "new-post", "new-thread", "new-story",
)

# What the site calls the control. Labels are the stronger signal of the two: a path can be
# incidental ("/new-york-times"), but a link a human reads as "Start a post" is one.
P_LABEL_RE = re.compile(
    r"\b(start a post|create a post|new post|create post|write a post|"
    r"ask (a )?question|new story|write a story|start writing|new thread|"
    r"compose|create new|new message|submit a? ?(post|link|text)?|publish)\b", re.I)

# Never a composer, and several are actively destructive to wander into mid-run. Checked against
# the whole URL plus the label, because "sign out" hides behind /logout as often as it is written.
P_NEVER_RE = re.compile(
    r"\b(log ?out|sign ?out|log ?in|sign ?in|sign ?up|register|settings|preferences|account|"
    r"billing|subscribe|upgrade|premium|checkout|cart|delete|privacy|terms|cookie|legal|"
    r"about|careers|jobs|advertise|press|help|support|download|api|developer)\b", re.I)


@typechecked
def enabled() -> bool:
    """OFF by default, unlike the compose-URL table it backs up.

    The mechanism is proven: pointed at StackOverflow it returned `/questions/ask` as its first
    candidate, which is exactly right. What is NOT proven is that it helps anyone end to end, and
    on the eight-site sweep it did not, for reasons outside itself: three of five create-sites
    publish no compose link at all (their composer is a button opening a modal with no route),
    StackOverflow was behind a sign-in wall, and GitHub never armed at an upstream gate. Shipping a
    tier default-on because its parts work, while its measured contribution is zero, is how latency
    accretes. It turns on when a site set exists where it can win and the number says it did."""
    return os.environ.get("OSW_COMPOSE_DISCOVERY", "0") != "0"


@typechecked
def discovery_expression() -> str:
    """One page read returning every link the site publishes, with the text a human would read.

    Deliberately read-only: it collects hrefs and labels and touches nothing, so it is safe to run
    on any page in any state, including one the user is looking at."""
    return (
        "(() => {"
        "  const out = []; const seen = new Set();"
        "  for (const a of document.querySelectorAll('a[href]')) {"
        "    const href = a.href || '';"
        "    if (!href || seen.has(href)) continue;"
        "    if (!/^https?:/i.test(href)) continue;"
        "    seen.add(href);"
        "    const label = (a.getAttribute('aria-label') || a.innerText || a.title || '')"
        "      .replace(/\\s+/g, ' ').trim().slice(0, 80);"
        "    out.push({href: href, label: label});"
        f"    if (out.length >= {MAX_LINKS}) break;"
        "  }"
        "  return {url: location.href, links: out};"
        "})()"
    )


@typechecked
def p_link_score(href: str, label: str, host: str, current_url: str) -> int:
    """How much this link looks like the way in to this site's composer. 0 means never navigate.

    Scored rather than matched so the front-door compose link outranks a deeper one that merely
    shares a word, which is what stops "/submit-a-tip" from beating "/submit"."""
    parsed = urlparse(href)
    found = compose_entry.registrable_host(parsed.netloc)
    want = compose_entry.registrable_host(host)
    # Off-host links go to a different company; a "share to X" button must not hijack a tumblr post.
    if not found or (found != want and not found.endswith("." + want)):
        return 0
    path = parsed.path.strip("/").lower()
    if not path:
        return 0
    if P_NEVER_RE.search(href) or P_NEVER_RE.search(label or ""):
        return 0
    # Already here. Re-navigating would remount the page and throw away whatever is on it.
    if href.rstrip("/") == (current_url or "").rstrip("/"):
        return 0
    score = 0
    # A compose control is labelled like a button, not like an article. Length is what separates
    # them, and it separates them on every site at once: StackOverflow offered a QUESTION titled
    # "Compose preview different from emulator" as a compose link, because a Q&A site is full of
    # titles containing the word. Buttons say "Ask Question" or "Start a post".
    if len((label or "").split()) <= MAX_LABEL_WORDS and P_LABEL_RE.search(label or ""):
        score += 10
    segments = [s for s in path.split("/") if s]
    if any(seg in P_PATH_HINTS for seg in segments):
        score += 6
    if not score:
        return 0
    # A shallow path is the site's own front door to composing; a deep one is usually a specific
    # item that happens to share a word. Never lets a match drop to zero.
    score += max(0, 3 - len(segments))
    return score


@typechecked
def rank_candidates(payload: Optional[Dict[str, object]], host: str) -> List[str]:
    """The URLs worth trying, best first, capped. Empty when the page publishes nothing composer-ish.

    Takes the raw page read so the whole decision is one pure function over data, which is the only
    reason this is testable without driving a browser."""
    if not isinstance(payload, dict):
        return []
    links = payload.get("links")
    if not isinstance(links, list):
        return []
    current = str(payload.get("url") or "")
    scored: List[Tuple[int, str]] = []
    seen: set = set()
    for row in links:
        if not isinstance(row, dict):
            continue
        href = str(row.get("href") or "")
        label = str(row.get("label") or "")
        if not href or href in seen:
            continue
        seen.add(href)
        score = p_link_score(href, label, host, current)
        if score > 0:
            scored.append((score, href))
    # Sort by score, then by URL so a tie is deterministic across runs rather than DOM-order luck.
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [href for _, href in scored[:MAX_CANDIDATES]]


@typechecked
def parse_page_read(raw: object) -> Optional[Dict[str, object]]:
    """The evaluate result, whatever shape the bridge handed back.

    BrowserEvaluate returns the value directly on some paths and JSON in a text field on others, and
    a discovery tier that silently sees nothing looks identical to a site with no compose link."""
    if isinstance(raw, dict) and "links" in raw:
        return raw
    if isinstance(raw, dict):
        for key in ("result", "value", "text"):
            inner = raw.get(key)
            if isinstance(inner, dict) and "links" in inner:
                return inner
            if isinstance(inner, str) and inner.strip().startswith("{"):
                try:
                    parsed = json.loads(inner)
                except ValueError:
                    continue
                if isinstance(parsed, dict) and "links" in parsed:
                    return parsed
    return None
