"""Discord channel scanner with LLM-based lead scoring."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

DISCORD_SCORE_PROMPT = """
You are a B2B lead qualification expert for Discord communities.
PRODUCT: {product_name}
DESCRIPTION: {product_description}

DISCORD MESSAGE:
Author: {author}
Content: {content}

Score 0-100 for purchase/adoption intent.
Reply ONLY: {{"score": <int>, "reasoning": "<1 sentence>"}}
""".strip()

# Type alias for the LLM function
LLMFn = Callable[..., Awaitable[dict[str, Any]]]


class DiscordScanner:
    """Fetches Discord channel messages and scores them via LLM."""

    DISCORD_API = "https://discord.com/api/v10"

    def __init__(self, bot_token: str, llm_fn: LLMFn | None = None) -> None:
        if not bot_token:
            raise ValueError("Discord bot token required")
        self._token = bot_token
        self._llm_fn = llm_fn

    async def fetch_messages(self, channel_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch recent messages from a Discord channel."""
        url = f"{self.DISCORD_API}/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {self._token}"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers=headers, params={"limit": min(limit, 100)})
                resp.raise_for_status()
                messages = resp.json()
                return [
                    {
                        "id": m.get("id", ""),
                        "content": m.get("content", ""),
                        "author": m.get("author", {}).get("username", ""),
                        "timestamp": m.get("timestamp", ""),
                    }
                    for m in messages
                    if m.get("content")
                ]
        except Exception as exc:
            log.warning("discord_fetch_failed", channel_id=channel_id, error=str(exc))
            return []

    async def score_message(
        self,
        message: dict[str, Any],
        product_name: str,
        product_description: str = "",
    ) -> tuple[int, str]:
        """Score a message for purchase/adoption intent 0-100 via LLM."""
        if not self._llm_fn:
            return 0, "No LLM available"

        prompt = DISCORD_SCORE_PROMPT.format(
            product_name=product_name,
            product_description=product_description,
            author=message.get("author", ""),
            content=message.get("content", "")[:1000],
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
            log.warning("discord_score_failed", error=str(exc))
            return 0, "Scoring failed"

    async def scan(
        self,
        channel_ids: list[str],
        product_name: str,
        product_description: str = "",
        min_score: int = 60,
    ) -> dict[str, Any]:
        """Scan multiple Discord channels: fetch messages, score, return leads."""
        all_leads: list[dict[str, Any]] = []
        total_checked = 0

        for i, channel_id in enumerate(channel_ids):
            if i > 0:
                await asyncio.sleep(1)
            messages = await self.fetch_messages(channel_id)
            total_checked += len(messages)
            for msg in messages:
                score, reasoning = await self.score_message(msg, product_name, product_description)
                if score >= min_score:
                    all_leads.append(
                        {
                            **msg,
                            "channel_id": channel_id,
                            "intent_score": score,
                            "score_reason": reasoning,
                        }
                    )

        return {
            "leads_found": len(all_leads),
            "posts_checked": total_checked,
            "leads": all_leads,
        }
