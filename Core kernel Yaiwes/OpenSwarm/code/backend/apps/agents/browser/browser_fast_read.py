"""
READ leg of the browser fast path: answer a public-page question with one
SSRF-guarded local fetch plus one cheap aux call, no browser and no
orchestrator. Anything short of a confident answer returns None and the
caller falls back to the full browser dispatch, so the worst case is the
old path, never a wrong answer from a thin read.
"""

import asyncio
import logging
import os
import re
import time
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

P_ENTRY_RE = re.compile(r"^ENTRY:\s*(https?://\S+)", re.I | re.M)
P_MIN_PAGE_CHARS = 500
MAX_PAGE_CHARS = 24000
P_FETCH_ERROR_PREFIXES = ("HTTP error", "Error fetching", "Refused to fetch")

ANSWER_SYSTEM = (
    "Answer the user's request using ONLY the page text provided. Be direct and "
    "complete in a few sentences; quote exact titles/values from the page. End "
    "with nothing else.\n"
    "If the page text does not contain what the request needs, reply with "
    "exactly the single word INSUFFICIENT."
)

# One-hop mode: same contract plus a FOLLOW escape so a link-deep answer costs one more fetch instead of a full browser dispatch.
P_HOP_SYSTEM = ANSWER_SYSTEM + (
    "\nEXCEPTION: if the page text is insufficient but exactly one of the "
    "numbered links clearly leads to the page that would contain the answer, "
    "reply with exactly 'FOLLOW <number>' and nothing else."
)
P_FOLLOW_RE = re.compile(r"^FOLLOW\s+(\d+)\s*$", re.I)
P_LINK_RE = re.compile(r"<a\b[^>]*?href=[\"'](?!javascript:|#|mailto:)([^\"'>]+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
P_MAX_LINKS = 60


def hop_enabled() -> bool:
    return os.environ.get("OSW_FASTREAD_HOP", "1") != "0"


def extract_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """(anchor text, absolute url) pairs, deduped, capped. Text-less anchors are
    useless to the picker so they're dropped."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for href, inner in P_LINK_RE.findall(html or ""):
        text = re.sub(r"<[^>]+>", " ", inner)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        absolute = urljoin(base_url, href.strip())
        if not absolute.startswith(("http://", "https://")) or absolute in seen:
            continue
        seen.add(absolute)
        out.append((text[:80], absolute))
        if len(out) >= P_MAX_LINKS:
            break
    return out


def format_link_menu(links: list[tuple[str, str]]) -> str:
    return "\n".join(f"{i + 1}. {text} -> {url}" for i, (text, url) in enumerate(links))


def parse_follow(answer: str, links: list[tuple[str, str]]) -> tuple[str, str]:
    """The (anchor text, url) the aux picked, or ('', ''). Out-of-range picks
    are dropped."""
    m = P_FOLLOW_RE.match((answer or "").strip())
    if not m:
        return "", ""
    idx = int(m.group(1)) - 1
    return links[idx] if 0 <= idx < len(links) else ("", "")


def extract_entry_url(brief: str) -> str:
    m = P_ENTRY_RE.search(brief or "")
    return m.group(1).rstrip(").,") if m else ""


def page_is_thin(text: str) -> bool:
    t = (text or "").strip()
    if not t or t.startswith(P_FETCH_ERROR_PREFIXES):
        return True
    body = t.split("\n\n", 1)[-1] if "\n\n" in t else t
    return len(body.strip()) < P_MIN_PAGE_CHARS


async def fetch_page_text(url: str, prompt: str) -> str:
    from backend.apps.agents.tools.web import WebFetchTool

    parts = await asyncio.wait_for(
        WebFetchTool().execute({"url": url, "prompt": prompt}, None),
        timeout=12.0,
    )
    return "\n".join(p.get("text", "") for p in parts if p.get("type") == "text")


P_TAG_STRIP_RES = (
    re.compile(r"<(script|style|noscript)\b.*?</\1>", re.I | re.S),
    re.compile(r"<[^>]+>"),
)


def strip_tags(html: str) -> str:
    """Whole-page text incl. bylines/usernames; trafilatura's main-content pass
    drops exactly the metadata that answers who/when questions, so hop mode
    reads the raw page instead."""
    import html as p_html_mod

    text = html or ""
    for rx in P_TAG_STRIP_RES:
        text = rx.sub(" ", text)
    return re.sub(r"[ \t\r\f\v]+", " ", p_html_mod.unescape(text)).strip()


async def fetch_raw(url: str) -> str:
    """Raw HTML via the SSRF guard; '' on any miss."""
    try:
        from backend.apps.agents.tools.ssrf_guard import safe_fetch

        resp = await asyncio.wait_for(
            safe_fetch(url, method="GET",
                       headers={"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36"},
                       timeout=8.0),
            timeout=10.0,
        )
        return resp.text or ""
    except Exception:
        return ""


async def ask_aux(client, aux_model: str, system: str, content: str) -> str:
    from backend.apps.agents.core.aux_llm import safe_resp_text

    resp = await asyncio.wait_for(
        client.messages.create(
            model=aux_model, max_tokens=500, temperature=0, system=system,
            messages=[{"role": "user", "content": content}],
        ),
        timeout=15.0,
    )
    return safe_resp_text(resp).strip()


async def try_fast_read(prompt: str, brief: str, settings, primary_api: str | None) -> str | None:
    """Answer text on success; None means fall back to the browser leg."""
    entry = extract_entry_url(brief)
    if not entry:
        logger.info("[browser-fast-read] no ENTRY url in brief; browser fallback")
        return None
    try:
        hop = hop_enabled()
        t0 = time.monotonic()
        links: list[tuple[str, str]] = []
        if hop:
            raw = await fetch_raw(entry)
            text, links = strip_tags(raw), extract_links(raw, entry)
            if page_is_thin(text):
                text = await fetch_page_text(entry, prompt)
        else:
            text = await fetch_page_text(entry, prompt)
        fetch_ms = int((time.monotonic() - t0) * 1000)
        if page_is_thin(text):
            logger.info(f"[browser-fast-read] thin/errored read of {entry} ({len(text)}ch in {fetch_ms}ms); browser fallback")
            return None
        logger.info(f"[browser-fast-read] fetched {entry}: {len(text)}ch in {fetch_ms}ms (links={len(links)})")

        from backend.apps.settings.credentials import get_anthropic_client_for_model
        from backend.apps.agents.providers.registry import resolve_aux_model

        aux_model, _ = await resolve_aux_model(
            settings, preferred_tier="haiku", primary_api=primary_api,
        )
        client = get_anthropic_client_for_model(settings, aux_model)
        t1 = time.monotonic()
        content = f"Request: {prompt}\n\nPage text from {entry}:\n{text[:MAX_PAGE_CHARS]}"
        if hop and links:
            content += f"\n\nNumbered links found on the page:\n{format_link_menu(links)}"
        answer = await ask_aux(client, aux_model, P_HOP_SYSTEM if links else ANSWER_SYSTEM, content)
        answer_ms = int((time.monotonic() - t1) * 1000)

        hop_anchor, hop_url = parse_follow(answer, links) if hop and links else ("", "")
        if hop_url:
            t2 = time.monotonic()
            hop_text = strip_tags(await fetch_raw(hop_url))
            if page_is_thin(hop_text):
                hop_text = await fetch_page_text(hop_url, prompt)
            if page_is_thin(hop_text):
                logger.info(f"[browser-fast-read] hop to {hop_url} was thin; browser fallback")
                return None
            answer = await ask_aux(
                client, aux_model, ANSWER_SYSTEM,
                f"Request: {prompt}\n\n"
                f"Context: the navigation in the request is ALREADY DONE. From {entry} "
                f"you chose the link '{hop_anchor}' as the one leading to the answer, and "
                f"the page text below is that destination. Extract the requested "
                f"information from it.\n\n"
                f"Page text from {hop_url}:\n{hop_text[:MAX_PAGE_CHARS]}",
            )
            logger.info(
                f"[browser-fast-read] followed link {hop_url} "
                f"(+{int((time.monotonic() - t2) * 1000)}ms hop)"
            )
            entry = hop_url

        if not answer or answer.upper().startswith("INSUFFICIENT") or P_FOLLOW_RE.match(answer):
            logger.info(f"[browser-fast-read] aux found page insufficient ({answer_ms}ms); browser fallback")
            return None
        logger.info(f"[browser-fast-read] answered in {answer_ms}ms ({len(answer)}ch, model={aux_model})")
        return f"{answer}\n\n(Source: {entry})"
    except Exception as e:
        logger.info(f"[browser-fast-read] failed ({e}); browser fallback")
        return None
