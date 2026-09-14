"""RSS/Atom feed scanner with LLM-based lead scoring.

Parses RSS 2.0 and Atom feeds using stdlib xml.etree, so no extra dependency
is introduced. Each entry is scored against the configured product by an LLM
function, and entries above the threshold are returned as leads.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

RSS_SCORE_PROMPT = """
You are a B2B lead qualification expert.
PRODUCT: {product_name}
DESCRIPTION: {product_description}

FEED ENTRY:
Title: {title}
Link: {url}
Summary: {summary}

Score 0-100 how relevant this entry is to the product. Only score high if the
entry describes a concrete need, pain point, or opportunity the product solves.
Reply ONLY with JSON: {{"score": <int>, "reasoning": "<1 sentence>"}}
""".strip()

LLMFn = Callable[..., Awaitable[dict[str, Any]]]

_ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _stable_entry_id(entry: dict[str, Any]) -> str:
    """Build a stable ID for an entry even when the feed omits <guid>/<id>."""
    basis = entry.get("id") or entry.get("url") or entry.get("title") or ""
    if not basis:
        return ""
    return hashlib.sha1(basis.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return (el.text or "").strip()


def parse_feed(xml_bytes: bytes) -> list[dict[str, Any]]:
    """Parse RSS 2.0 or Atom feed bytes into a list of entry dicts.

    Returns an empty list on malformed XML rather than raising — callers treat
    a failed fetch as "no new items" and move on to the next feed.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        log.warning("rss_parse_failed", error=str(exc))
        return []

    entries: list[dict[str, Any]] = []

    # RSS 2.0: <rss><channel><item>
    for item in root.findall(".//item"):
        title = _text(item.find("title"))
        link = _text(item.find("link"))
        description = _text(item.find("description"))
        guid = _text(item.find("guid"))
        pub = _text(item.find("pubDate"))
        if not title and not link:
            continue
        entries.append(
            {
                "id": guid or link,
                "title": title,
                "url": link,
                "summary": description,
                "published": pub,
            }
        )

    # Atom: <feed><entry>
    for entry in root.findall(f".//{_ATOM_NS}entry"):
        title = _text(entry.find(f"{_ATOM_NS}title"))
        link_el = entry.find(f"{_ATOM_NS}link")
        link = (link_el.get("href") if link_el is not None else "") or ""
        summary = _text(entry.find(f"{_ATOM_NS}summary")) or _text(entry.find(f"{_ATOM_NS}content"))
        entry_id = _text(entry.find(f"{_ATOM_NS}id"))
        updated = _text(entry.find(f"{_ATOM_NS}updated"))
        if not title and not link:
            continue
        entries.append(
            {
                "id": entry_id or link,
                "title": title,
                "url": link,
                "summary": summary,
                "published": updated,
            }
        )

    return entries


class RssFeedScanner:
    """Fetches RSS/Atom feeds and scores entries via LLM."""

    def __init__(self, llm_fn: LLMFn | None = None) -> None:
        self._llm_fn = llm_fn

    async def fetch_feed(self, url: str, limit: int = 30) -> list[dict[str, Any]]:
        """Fetch and parse a single feed. Returns at most ``limit`` entries."""
        try:
            async with httpx.AsyncClient(
                timeout=30, follow_redirects=True, headers={"User-Agent": "Cognithor/1.0"}
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                entries = parse_feed(resp.content)
        except Exception as exc:
            log.warning("rss_fetch_failed", url=url, error=str(exc))
            return []
        for entry in entries:
            entry["feed_url"] = url
            entry["entry_hash"] = _stable_entry_id(entry)
        return entries[:limit]

    async def score_entry(
        self,
        entry: dict[str, Any],
        product_name: str,
        product_description: str = "",
    ) -> tuple[int, str]:
        """Score a feed entry for relevance 0-100 via LLM."""
        if not self._llm_fn:
            return 0, "No LLM available"

        prompt = RSS_SCORE_PROMPT.format(
            product_name=product_name,
            product_description=product_description,
            title=entry.get("title", ""),
            url=entry.get("url", ""),
            summary=(entry.get("summary", "") or "")[:800],
        )
        try:
            response = await self._llm_fn(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = response.get("message", {}).get("content", "")
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                return 0, "No JSON in LLM response"
            data = json.loads(raw[start:end])
            score = max(0, min(100, int(data.get("score", 0))))
            reasoning = str(data.get("reasoning", ""))
            return score, reasoning
        except Exception as exc:
            log.warning("rss_score_failed", error=str(exc))
            return 0, "Scoring failed"

    async def scan(
        self,
        feeds: list[str],
        product_name: str,
        product_description: str = "",
        min_score: int = 60,
    ) -> dict[str, Any]:
        """Run a full scan: fetch feeds, deduplicate, score, return leads."""
        seen: dict[str, dict[str, Any]] = {}
        for feed_url in feeds:
            entries = await self.fetch_feed(feed_url, limit=30)
            for entry in entries:
                key = entry.get("entry_hash") or entry.get("url") or ""
                if key and key not in seen:
                    seen[key] = entry
            await asyncio.sleep(0.5)

        leads: list[dict[str, Any]] = []
        for entry in seen.values():
            score, reasoning = await self.score_entry(entry, product_name, product_description)
            if score >= min_score:
                leads.append(
                    {
                        **entry,
                        "intent_score": score,
                        "score_reason": reasoning,
                    }
                )

        return {
            "leads_found": len(leads),
            "posts_checked": len(seen),
            "leads": leads,
        }
