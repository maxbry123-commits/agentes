from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import TYPE_CHECKING, Any

from cognithor.memory.cag.content_normalizer import ContentNormalizer
from cognithor.memory.cag.models import (
    CacheEntry,
    CAGMetrics,
    CAGRefreshReport,
    CAGStatus,
)

if TYPE_CHECKING:
    from cognithor.memory.cag.builders.base import CacheBuilder
    from cognithor.memory.cag.cache_store import CacheStore
    from cognithor.memory.cag.metrics import CAGMetricsCollector
    from cognithor.memory.cag.selectors import CAGSelector

logger = logging.getLogger(__name__)


class CAGManager:
    """Orchestrates the CAG layer: select, normalize, cache, build prefix."""

    def __init__(
        self,
        config: Any,
        cache_store: CacheStore,
        builder: CacheBuilder,
        selector: CAGSelector,
        metrics_collector: CAGMetricsCollector,
    ) -> None:
        self._config = config
        self._store = cache_store
        self._builder = builder
        self._selector = selector
        self._metrics = metrics_collector
        self._lock = asyncio.Lock()
        self._last_prefix: str | None = None
        self._last_prefix_hash: str = ""

    @property
    def is_active(self) -> bool:
        """True if enabled in config."""
        return getattr(self._config, "enabled", False)

    async def build_all(self, core_memory_text: str, model_id: str) -> CAGRefreshReport:
        """Select eligible content, normalize, hash, store. Only rebuild if changed."""
        async with self._lock:
            t0 = time.monotonic()
            refreshed: list[str] = []
            unchanged: list[str] = []
            failed: list[tuple[str, str]] = []

            candidates = self._selector.select(core_memory_text)

            for candidate in candidates:
                cid = candidate["cache_id"]
                try:
                    normalized = ContentNormalizer.normalize(candidate["content"])
                    content_hash = ContentNormalizer.compute_hash(normalized)

                    existing = self._store.load(cid)
                    if existing and existing.content_hash == content_hash:
                        unchanged.append(cid)
                        continue

                    entry = CacheEntry(
                        cache_id=cid,
                        content_hash=content_hash,
                        normalized_text=normalized,
                        token_count=len(normalized.split()),
                        source_tier=candidate.get("source_tier", "core"),
                        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        model_id=model_id,
                    )
                    self._store.save(entry)
                    refreshed.append(cid)
                except Exception as exc:
                    logger.debug("cag_build_entry_failed", exc_info=True)
                    failed.append((cid, str(exc)))

            # Build prefix from all entries
            entries = self._store.list_entries()
            if entries:
                self._last_prefix = await self._builder.prepare_prefix(entries, model_id)

            # Update metrics
            duration_ms = (time.monotonic() - t0) * 1000
            self._metrics.record_build(duration_ms)
            self._metrics._metrics.cache_entries = len(entries) if entries else 0
            self._metrics._metrics.total_cached_tokens = (
                sum(e.token_count for e in entries) if entries else 0
            )

            return CAGRefreshReport(
                refreshed=refreshed,
                unchanged=unchanged,
                failed=failed,
            )

    async def get_stable_prefix(self, core_memory_text: str, model_id: str) -> str | None:
        """Return stable prefix. Auto-build if needed. Track hit/miss."""
        if not self.is_active:
            return None

        entries = self._store.list_entries()

        # If no entries yet, build all first
        if not entries:
            await self.build_all(core_memory_text, model_id)
            entries = self._store.list_entries()
            if not entries:
                return None

        # Check if content changed
        needs_rebuild = False
        for entry in entries:
            if ContentNormalizer.has_changed(entry.content_hash, core_memory_text):
                needs_rebuild = True
                break

        if needs_rebuild and getattr(self._config, "auto_rebuild_on_change", True):
            await self.build_all(core_memory_text, model_id)
            entries = self._store.list_entries()

        if not entries:
            return None

        prefix = await self._builder.prepare_prefix(entries, model_id)
        prefix_hash = hashlib.sha256(prefix.encode("utf-8")).hexdigest()

        if prefix_hash == self._last_prefix_hash and self._last_prefix_hash:
            self._metrics.record_hit(prefix_hash)
        else:
            self._metrics.record_miss(prefix_hash)

        self._last_prefix = prefix
        self._last_prefix_hash = prefix_hash
        return prefix

    async def invalidate(self, cache_id: str) -> None:
        """Delete a cache entry."""
        self._store.delete(cache_id)
        self._last_prefix = None
        self._last_prefix_hash = ""

    async def get_status(self) -> CAGStatus:
        """Return current CAG status."""
        entries = self._store.list_entries()
        metrics = self._metrics.get_metrics()
        return CAGStatus(
            enabled=self.is_active,
            backend=getattr(self._config, "backend", "prefix"),
            entries=entries,
            metrics=metrics,
        )

    async def get_metrics(self) -> CAGMetrics:
        """Return current metrics snapshot."""
        return self._metrics.get_metrics()
