"""MC08 parcial · cache in-memory con invalidación por memory_version."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from memory.versioning import CacheKey


@dataclass
class CacheEntry:
    value: Any
    memory_version: int


class SimpleCache:
    def __init__(self) -> None:
        self._store: Dict[str, CacheEntry] = {}

    def get(self, key: CacheKey, *, current_version: int) -> Any | None:
        e = self._store.get(key.value)
        if e is None:
            return None
        if e.memory_version != current_version:
            del self._store[key.value]
            return None
        return e.value

    def set(self, key: CacheKey, value: Any, *, memory_version: int) -> None:
        self._store[key.value] = CacheEntry(value=value, memory_version=memory_version)

    def clear(self) -> None:
        self._store.clear()
