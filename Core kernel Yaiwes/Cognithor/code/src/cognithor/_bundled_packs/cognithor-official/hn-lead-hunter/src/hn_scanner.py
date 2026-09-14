"""Hacker News story scanner with LLM-based lead scoring."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

HN_SCORE_PROMPT = """
You are a B2B lead qualification expert for Hacker News.
PRODUCT: {product_name}
DESCRIPTION: {product_description}

HACKER NEWS STORY:
Title: {title}
URL: {url}
Points: {score}
Comments: {descendants}

Score 0-100 for relevance. HN values technical depth, not marketing.
Reply ONLY: {{"score": <int>, "reasoning": "<1 sentence>"}}
""".strip()

_CATEGORY_MAP = {
    "top": "topstories",
    "new": "newstories",
    "best": "beststories",
}

# Type alias for the LLM function
LLMFn = Callable[..., Awaitable[dict[str, Any]]]


class HackerNewsScanner:
    """Fetches Hacker News stories and scores them via LLM."""

    HN_API = "https://hacker-news.firebaseio.com/v0"
    ALGOLIA_API = "https://hn.algolia.com/api/v1"

    def __init__(self, llm_fn: LLMFn | None = None) -> None:
        self._llm_fn = llm_fn

    async def fetch_stories(self, category: str = "top", limit: int = 30) -> list[dict[str, Any]]:
        """Fetch stories from HN by category (top/new/best)."""
        endpoint = _CATEGORY_MAP.get(category, "topstories")
        url = f"{self.HN_API}/{endpoint}.json"
        stories: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                ids = resp.json()
                for story_id in ids[:limit]:
                    try:
                        item_resp = await client.get(f"{self.HN_API}/item/{story_id}.json")
                        item_resp.raise_for_status()
                        item = item_resp.json()
                        if item and item.get("type") == "story":
                            stories.append(
                                {
                                    "id": item.get("id", 0),
                                    "title": item.get("title", ""),
                                    "url": item.get("url", ""),
                                    "score": item.get("score", 0),
                                    "descendants": item.get("descendants", 0),
                                    "time": item.get("time", 0),
                                    "by": item.get("by", ""),
                                }
                            )
                    except Exception as exc:
                        log.warning(
                            "hn_item_fetch_failed",
                            story_id=story_id,
                            error=str(exc),
                        )
                    await asyncio.sleep(0.5)
        except Exception as exc:
            log.warning("hn_fetch_failed", category=category, error=str(exc))
        return stories

    async def search_stories(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search HN stories via Algolia API."""
        url = f"{self.ALGOLIA_API}/search"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    url,
                    params={"query": query, "tags": "story", "hitsPerPage": limit},
                )
                resp.raise_for_status()
                hits = resp.json().get("hits", [])
                return [
                    {
                        "objectID": h.get("objectID", ""),
                        "title": h.get("title", ""),
                        "url": h.get("url", ""),
                        "points": h.get("points", 0),
                        "num_comments": h.get("num_comments", 0),
                        "author": h.get("author", ""),
                    }
                    for h in hits
                ]
        except Exception as exc:
            log.warning("hn_search_failed", query=query, error=str(exc))
            return []

    async def score_story(
        self,
        story: dict[str, Any],
        product_name: str,
        product_description: str = "",
    ) -> tuple[int, str]:
        """Score a story for relevance 0-100 via LLM."""
        if not self._llm_fn:
            return 0, "No LLM available"

        prompt = HN_SCORE_PROMPT.format(
            product_name=product_name,
            product_description=product_description,
            title=story.get("title", ""),
            url=story.get("url", ""),
            score=story.get("score", story.get("points", 0)),
            descendants=story.get("descendants", story.get("num_comments", 0)),
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
            log.warning("hn_score_failed", error=str(exc))
            return 0, "Scoring failed"

    async def scan(
        self,
        product_name: str,
        product_description: str = "",
        categories: list[str] | None = None,
        min_score: int = 60,
    ) -> dict[str, Any]:
        """Run a full scan: fetch stories, deduplicate, score, return leads."""
        if categories is None:
            categories = ["top", "new"]

        all_stories: dict[int, dict[str, Any]] = {}
        for cat in categories:
            stories = await self.fetch_stories(category=cat, limit=30)
            for s in stories:
                sid = s.get("id", 0)
                if sid and sid not in all_stories:
                    all_stories[sid] = s

        leads: list[dict[str, Any]] = []
        for story in all_stories.values():
            score, reasoning = await self.score_story(story, product_name, product_description)
            if score >= min_score:
                leads.append(
                    {
                        **story,
                        "intent_score": score,
                        "score_reason": reasoning,
                    }
                )

        return {
            "leads_found": len(leads),
            "posts_checked": len(all_stories),
            "leads": leads,
        }
