from __future__ import annotations

from cognithor.memory.cag.models import CAGMetrics


class CAGMetricsCollector:
    """Collects hit/miss/build metrics for the CAG layer."""

    def __init__(self) -> None:
        self._metrics = CAGMetrics()

    def record_hit(self, prefix_hash: str) -> None:
        self._metrics.prefix_hits += 1
        self._metrics.last_prefix_hash = prefix_hash

    def record_miss(self, prefix_hash: str) -> None:
        self._metrics.prefix_misses += 1
        self._metrics.last_prefix_hash = prefix_hash

    def record_build(self, duration_ms: float) -> None:
        self._metrics.total_builds += 1
        self._metrics.total_build_ms += duration_ms

    def get_metrics(self) -> CAGMetrics:
        """Return a snapshot of current metrics."""
        return CAGMetrics(
            prefix_hits=self._metrics.prefix_hits,
            prefix_misses=self._metrics.prefix_misses,
            total_builds=self._metrics.total_builds,
            total_build_ms=self._metrics.total_build_ms,
            last_prefix_hash=self._metrics.last_prefix_hash,
            cache_entries=self._metrics.cache_entries,
            total_cached_tokens=self._metrics.total_cached_tokens,
        )

    def reset(self) -> None:
        self._metrics = CAGMetrics()
