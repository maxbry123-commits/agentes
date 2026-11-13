"""Unified MCP tools for cross-platform social listening.

Works with the source-agnostic cognithor.leads.LeadService.
Individual scan sources (Reddit, HN, Discord, RSS) are provided
by agent packs that register a LeadSource via PackContext.leads.
"""

from __future__ import annotations

import json
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


def register_social_tools(mcp_client: Any, lead_service: Any) -> None:
    """Register social_scan and social_leads MCP tools."""

    async def _social_scan(
        platform: str = "",
        product: str = "",
        subreddits: str = "",
        categories: str = "",
        channel_ids: str = "",
        min_score: int = 0,
    ) -> str:
        """Scan social platforms for leads.

        platform: reddit|hackernews|discord|rss|'' (all enabled)
        """
        if lead_service is None:
            return json.dumps({"error": "Social listening not initialized"})

        _min = min_score or 60
        _source_id: str | None = platform or None

        # Build per-source config from legacy parameters
        _config: dict[str, Any] = {}
        if subreddits:
            _config["reddit"] = {
                "subreddits": [s.strip() for s in subreddits.split(",") if s.strip()]
            }
        if categories:
            _config["hackernews"] = {
                "categories": [c.strip() for c in categories.split(",") if c.strip()]
            }
        if channel_ids:
            _config["discord"] = {
                "channel_ids": [c.strip() for c in channel_ids.split(",") if c.strip()]
            }

        try:
            result = await lead_service.scan(
                source_id=_source_id,
                min_score=_min,
                product=product,
                config=_config,
                trigger="chat",
            )
            return json.dumps(
                {
                    "leads_found": result.leads_found,
                    "posts_checked": result.posts_checked,
                    "summary": result.summary(),
                },
                ensure_ascii=False,
            )
        except ValueError as exc:
            return json.dumps({"error": str(exc)})
        except Exception as exc:
            log.warning("social_scan_failed", error=str(exc), exc_info=True)
            return json.dumps({"error": str(exc)})

    async def _social_leads(
        platform: str = "",
        status: str = "",
        min_score: int = 0,
        limit: int = 20,
    ) -> str:
        """List leads from all platforms with optional filters."""
        if lead_service is None:
            return json.dumps({"error": "Social listening not initialized"})
        leads = lead_service.get_leads(
            source_id=platform or None,
            status=status or None,
            min_score=min_score,
            limit=limit,
        )
        return json.dumps(
            {
                "count": len(leads),
                "leads": [
                    {
                        "id": l.id,
                        "platform": getattr(l, "source_id", getattr(l, "platform", "")),
                        "score": l.intent_score,
                        "title": l.title[:80],
                        "status": l.status.value if hasattr(l.status, "value") else l.status,
                        "url": getattr(l, "platform_url", None) or getattr(l, "url", ""),
                    }
                    for l in leads
                ],
            },
            ensure_ascii=False,
        )

    # Register with proper JSON Schema
    mcp_client.register_builtin_handler(
        "social_scan",
        _social_scan,
        description="Scanne soziale Plattformen nach Leads (Reddit, Hacker News, Discord, RSS)",
        input_schema={
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "reddit, hackernews, discord, rss, oder leer fuer alle",
                },
                "product": {"type": "string", "description": "Produktname"},
                "subreddits": {
                    "type": "string",
                    "description": "Reddit: kommagetrennte Subreddit-Namen",
                },
                "categories": {
                    "type": "string",
                    "description": "HN: top,new,best",
                },
                "channel_ids": {
                    "type": "string",
                    "description": "Discord: kommagetrennte Channel-IDs",
                },
                "min_score": {
                    "type": "integer",
                    "description": "Minimum Score 0-100",
                },
            },
        },
    )

    mcp_client.register_builtin_handler(
        "social_leads",
        _social_leads,
        description="Leads von allen Plattformen auflisten mit optionalen Filtern",
        input_schema={
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "Filter: reddit, hackernews, discord, rss",
                },
                "status": {
                    "type": "string",
                    "description": "Filter: new, reviewed, replied, archived",
                },
                "min_score": {
                    "type": "integer",
                    "description": "Minimum Score",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max Ergebnisse (Default: 20)",
                },
            },
        },
    )
    log.info("social_tools_registered", tools=2)
