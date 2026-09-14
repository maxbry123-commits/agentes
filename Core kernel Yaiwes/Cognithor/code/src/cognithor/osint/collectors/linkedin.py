"""LinkedIn collector — STUB (Phase 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cognithor.osint.collectors.base import BaseCollector

if TYPE_CHECKING:
    from cognithor.osint.models import Evidence


class LinkedInCollector(BaseCollector):
    source_name = "linkedin"

    def is_available(self) -> bool:
        return False

    async def collect(self, target: str, claims: list[str]) -> list[Evidence]:
        return []
