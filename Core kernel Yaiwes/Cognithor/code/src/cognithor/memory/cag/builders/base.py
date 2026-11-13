from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cognithor.memory.cag.models import CacheEntry


class CacheBuilder(ABC):
    """Abstract base for CAG cache builders."""

    @abstractmethod
    async def prepare_prefix(self, entries: list[CacheEntry], model_id: str) -> str:
        """Build a deterministic prefix string from cache entries."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the builder backend is usable."""

    @abstractmethod
    def supports_native_state(self) -> bool:
        """Return True if the builder can save/load native KV-cache state."""
