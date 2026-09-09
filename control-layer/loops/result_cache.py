"""Result Cache L1/L2/L3 · 0% LLM
SOURCE: Fase 5 · fingerprint → reuse
"""
from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass
from typing import Any


def fingerprint(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@dataclass
class CacheEntry:
    key: str
    value: Any
    level: str  # L1|L2|L3
    expires_at: float  # epoch


class ResultCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    def put(self, key: str, value: Any, level: str = "L1", ttl_seg: int = 3600) -> None:
        self._store[key] = CacheEntry(key=key, value=value, level=level, expires_at=time.time() + ttl_seg)

    def get(self, key: str) -> Any | None:
        e = self._store.get(key)
        if not e:
            return None
        if time.time() > e.expires_at:
            self._store.pop(key, None)
            return None
        return e.value

    def invalidate(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def clear_level(self, level: str) -> int:
        keys = [k for k, e in self._store.items() if e.level == level]
        for k in keys:
            del self._store[k]
        return len(keys)
