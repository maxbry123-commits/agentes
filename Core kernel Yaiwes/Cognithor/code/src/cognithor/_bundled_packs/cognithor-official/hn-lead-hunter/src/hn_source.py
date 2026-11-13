"""Hacker News LeadSource adapter."""

from __future__ import annotations

from typing import Any

from hn_scanner import HackerNewsScanner

from cognithor.leads.models import Lead
from cognithor.leads.source import LeadSource


class HnLeadSource(LeadSource):
    source_id = "hn"
    display_name = "Hacker News"
    icon = "article"
    color = "#FF6600"
    capabilities = frozenset({"scan"})

    def __init__(self, llm_fn: Any = None) -> None:
        self._scanner = HackerNewsScanner(llm_fn=llm_fn)

    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        categories = list(config.get("categories") or ["top", "new"])
        raw = await self._scanner.scan(
            product_name=product,
            product_description=product_description,
            categories=categories,
            min_score=min_score,
        )
        return [
            Lead(
                post_id=f"hn-{entry.get('id', '')}",
                source_id="hn",
                title=entry.get("title", ""),
                url=entry.get("url", "")
                or f"https://news.ycombinator.com/item?id={entry.get('id', '')}",
                intent_score=entry.get("intent_score", 0),
                score_reason=entry.get("score_reason", ""),
            )
            for entry in raw.get("leads", [])
        ]
