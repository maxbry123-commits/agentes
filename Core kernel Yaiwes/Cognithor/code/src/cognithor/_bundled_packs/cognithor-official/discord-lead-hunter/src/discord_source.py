"""Discord LeadSource adapter."""

from __future__ import annotations

import os
from typing import Any

from discord_scanner import DiscordScanner

from cognithor.leads.models import Lead
from cognithor.leads.source import LeadSource


class DiscordLeadSource(LeadSource):
    source_id = "discord"
    display_name = "Discord"
    icon = "tag"
    color = "#5865F2"
    capabilities = frozenset({"scan"})

    def __init__(self, llm_fn: Any = None) -> None:
        self._llm_fn = llm_fn

    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        bot_token = os.environ.get("COGNITHOR_DISCORD_TOKEN", "")
        if not bot_token:
            return []

        scanner = DiscordScanner(bot_token=bot_token, llm_fn=self._llm_fn)
        channel_ids = list(config.get("channel_ids") or [])
        if not channel_ids:
            return []

        raw = await scanner.scan(
            channel_ids=channel_ids,
            product_name=product,
            product_description=product_description,
            min_score=min_score,
        )
        return [
            Lead(
                post_id=f"discord-{entry.get('id', '')}",
                source_id="discord",
                title=entry.get("content", "")[:120],
                url=(
                    f"https://discord.com/channels/@me/"
                    f"{entry.get('channel_id', '')}/{entry.get('id', '')}"
                ),
                intent_score=entry.get("intent_score", 0),
                score_reason=entry.get("score_reason", ""),
            )
            for entry in raw.get("leads", [])
        ]
