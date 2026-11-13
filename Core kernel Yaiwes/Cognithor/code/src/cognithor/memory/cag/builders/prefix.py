from __future__ import annotations

from typing import TYPE_CHECKING

from cognithor.memory.cag.builders.base import CacheBuilder

if TYPE_CHECKING:
    from cognithor.memory.cag.models import CacheEntry


class PrefixCacheBuilder(CacheBuilder):
    """Builds a deterministic text prefix from CAG cache entries."""

    async def prepare_prefix(self, entries: list[CacheEntry], model_id: str) -> str:
        """Sort entries by cache_id, format each as [CAG:<id>] block, join."""
        if not entries:
            return ""
        sorted_entries = sorted(entries, key=lambda e: e.cache_id)
        blocks = [f"[CAG:{e.cache_id}]\n{e.normalized_text}" for e in sorted_entries]
        return "\n\n".join(blocks)

    async def is_available(self) -> bool:
        return True

    def supports_native_state(self) -> bool:
        return False
