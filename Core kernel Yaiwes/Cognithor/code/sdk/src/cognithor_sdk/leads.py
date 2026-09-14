"""Lead source interfaces — standalone copy of cognithor.leads."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar


class LeadStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    REPLIED = "replied"
    ARCHIVED = "archived"


@dataclass
class Lead:
    post_id: str
    source_id: str
    title: str
    url: str
    intent_score: int
    body: str = ""
    author: str = ""
    created_utc: float = 0.0
    score_reason: str = ""
    reply_draft: str = ""
    status: LeadStatus = LeadStatus.NEW
    scan_id: str = ""
    received_at: float = field(default_factory=time.time)
    subreddit: str = ""
    upvotes: int = 0
    num_comments: int = 0


class LeadSource(ABC):
    source_id: ClassVar[str]
    display_name: ClassVar[str]
    icon: ClassVar[str]
    color: ClassVar[str]
    capabilities: ClassVar[frozenset[str]]

    @abstractmethod
    async def scan(
        self,
        *,
        config: dict[str, Any],
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]: ...

    async def draft_reply(self, lead: Lead, *, tone: str) -> str:
        raise NotImplementedError

    async def refine_reply(self, lead: Lead, draft: str) -> str:
        raise NotImplementedError

    async def post_reply(self, lead: Lead, text: str) -> None:
        raise NotImplementedError
