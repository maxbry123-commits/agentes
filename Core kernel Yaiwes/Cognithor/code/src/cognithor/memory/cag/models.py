from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CacheEntry:
    cache_id: str  # e.g. "core_memory"
    content_hash: str  # sha256 of normalized content
    normalized_text: str  # stable deterministic text
    token_count: int
    source_tier: str  # "core", "semantic", "procedural"
    created_at: str  # ISO 8601
    model_id: str  # model this was prepared for


@dataclass
class CAGMetrics:
    prefix_hits: int = 0
    prefix_misses: int = 0
    total_builds: int = 0
    total_build_ms: float = 0.0
    last_prefix_hash: str = ""
    cache_entries: int = 0
    total_cached_tokens: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.prefix_hits + self.prefix_misses
        return self.prefix_hits / total if total > 0 else 0.0


@dataclass(frozen=True)
class CAGStatus:
    enabled: bool
    backend: str
    entries: list[CacheEntry]
    metrics: CAGMetrics


@dataclass(frozen=True)
class CAGRefreshReport:
    refreshed: list[str]  # cache_ids rebuilt
    unchanged: list[str]  # same hash, skipped
    failed: list[tuple[str, str]]  # (cache_id, error)
