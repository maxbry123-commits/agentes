# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Hashline Guard — LRU file cache with thread safety."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import TYPE_CHECKING

from cognithor.hashline.config import HashlineConfig
from cognithor.hashline.models import CacheStats, HashlinedFile
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger(__name__)


class HashlineCache:
    """Thread-safe LRU cache for hashlined file data.

    Stores ``HashlinedFile`` instances keyed by resolved absolute path.
    Evicts the least-recently-used entry when the cache exceeds its
    configured maximum size.

    Args:
        config: Hashline configuration providing ``cache_max_files``
            and ``stale_threshold_seconds``.
    """

    def __init__(self, config: HashlineConfig | None = None) -> None:
        self._config = config or HashlineConfig.default()
        self._store: OrderedDict[Path, HashlinedFile] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, path: Path) -> HashlinedFile | None:
        """Retrieve a cached file, promoting it in LRU order.

        Args:
            path: File path (will be resolved to absolute).

        Returns:
            The cached ``HashlinedFile`` or ``None`` if not present.
        """
        key = path.resolve()
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                self._hits += 1
                return self._store[key]
            self._misses += 1
            return None

    def put(self, path: Path, data: HashlinedFile) -> None:
        """Insert or update a file in the cache, evicting LRU if full.

        Args:
            path: File path (will be resolved to absolute).
            data: The hashlined file data to cache.
        """
        key = path.resolve()
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                self._store[key] = data
            else:
                if len(self._store) >= self._config.cache_max_files:
                    evicted_key, _ = self._store.popitem(last=False)
                    self._evictions += 1
                    log.debug("Cache evicted: %s", evicted_key)
                self._store[key] = data

    def invalidate(self, path: Path) -> bool:
        """Remove a single file from the cache.

        Args:
            path: File path to invalidate.

        Returns:
            True if the entry was found and removed.
        """
        key = path.resolve()
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def invalidate_all(self) -> int:
        """Remove all entries from the cache.

        Returns:
            The number of entries that were removed.
        """
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def contains(self, path: Path) -> bool:
        """Check if a path is in the cache.

        Args:
            path: File path to check.

        Returns:
            True if the path is cached.
        """
        key = path.resolve()
        with self._lock:
            return key in self._store

    def is_stale(self, path: Path) -> bool:
        """Check if a cached entry has exceeded the staleness threshold.

        Args:
            path: File path to check.

        Returns:
            True if the entry is stale or not present.
        """
        key = path.resolve()
        with self._lock:
            if key not in self._store:
                return True
            entry = self._store[key]
            age = time.time() - entry.read_timestamp
            return age > self._config.stale_threshold_seconds

    @property
    def stats(self) -> CacheStats:
        """Return current cache statistics.

        Returns:
            A ``CacheStats`` dataclass with hits, misses, evictions, and size.
        """
        with self._lock:
            return CacheStats(
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                size=len(self._store),
            )
