"""RSS/Atom LeadSource adapter."""

from __future__ import annotations

from typing import Any

from rss_scanner import RssFeedScanner

from cognithor.leads.models import Lead
from cognithor.leads.source import LeadSource


class RssLeadSource(LeadSource):
    source_id = "rss"
    display_name = "RSS / Atom Feeds"
    icon = "rss_feed"
    color = "#FFA500"
    capabilities = frozenset({"scan"})

    def __init__(self, llm_fn: Any = None) -> None:
        self._scanner = RssFeedScanner(llm_fn=llm_fn)

    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        feeds = list(config.get("feeds") or [])
        if not feeds:
            return []

        raw = await self._scanner.scan(
            feeds=feeds,
            product_name=product,
            product_description=product_description,
            min_score=min_score,
        )
        return [
            Lead(
                post_id=f"rss-{entry.get('entry_hash', '') or entry.get('id', '')}",
                source_id="rss",
                title=entry.get("title", ""),
                url=entry.get("url", ""),
                intent_score=entry.get("intent_score", 0),
                score_reason=entry.get("score_reason", ""),
            )
            for entry in raw.get("leads", [])
        ]
