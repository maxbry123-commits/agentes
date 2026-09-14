# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for Hashline Guard cache."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from cognithor.hashline.cache import HashlineCache
from cognithor.hashline.config import HashlineConfig
from cognithor.hashline.models import HashlinedFile, HashlinedLine

if TYPE_CHECKING:
    from pathlib import Path


def _make_file(path: Path, timestamp: float | None = None) -> HashlinedFile:
    """Helper to create a minimal HashlinedFile."""
    return HashlinedFile(
        path=path,
        lines=[HashlinedLine(number=1, content="x", hash_tag="AB", full_hash="0" * 16)],
        file_hash="a" * 64,
        read_timestamp=timestamp or time.time(),
        encoding="utf-8",
    )


class TestCacheBasicOps:
    def test_put_and_get(self, cache: HashlineCache, tmp_path: Path) -> None:
        p = tmp_path / "a.py"
        p.write_text("hello", encoding="utf-8")
        data = _make_file(p)
        cache.put(p, data)
        assert cache.get(p) is data

    def test_get_missing(self, cache: HashlineCache, tmp_path: Path) -> None:
        p = tmp_path / "missing.py"
        assert cache.get(p) is None

    def test_contains(self, cache: HashlineCache, tmp_path: Path) -> None:
        p = tmp_path / "b.py"
        p.write_text("x", encoding="utf-8")
        assert not cache.contains(p)
        cache.put(p, _make_file(p))
        assert cache.contains(p)

    def test_invalidate(self, cache: HashlineCache, tmp_path: Path) -> None:
        p = tmp_path / "c.py"
        p.write_text("x", encoding="utf-8")
        cache.put(p, _make_file(p))
        assert cache.invalidate(p) is True
        assert cache.get(p) is None
        assert cache.invalidate(p) is False

    def test_invalidate_all(self, cache: HashlineCache, tmp_path: Path) -> None:
        for name in ("a.py", "b.py", "c.py"):
            p = tmp_path / name
            p.write_text("x", encoding="utf-8")
            cache.put(p, _make_file(p))
        count = cache.invalidate_all()
        assert count == 3
        assert cache.stats.size == 0


class TestCacheLRU:
    def test_eviction(self, small_cache: HashlineCache, tmp_path: Path) -> None:
        paths = []
        for i in range(4):
            p = tmp_path / f"file{i}.py"
            p.write_text(f"content {i}", encoding="utf-8")
            paths.append(p)
            small_cache.put(p, _make_file(p))

        # First file should be evicted (max=3)
        assert small_cache.get(paths[0]) is None
        assert small_cache.get(paths[1]) is not None
        assert small_cache.stats.evictions == 1

    def test_access_promotes(self, small_cache: HashlineCache, tmp_path: Path) -> None:
        paths = []
        for i in range(3):
            p = tmp_path / f"file{i}.py"
            p.write_text(f"content {i}", encoding="utf-8")
            paths.append(p)
            small_cache.put(p, _make_file(p))

        # Access file0 to promote it
        small_cache.get(paths[0])

        # Add a 4th file — file1 should be evicted (oldest unreferenced)
        p = tmp_path / "file3.py"
        p.write_text("content 3", encoding="utf-8")
        small_cache.put(p, _make_file(p))

        assert small_cache.get(paths[0]) is not None
        assert small_cache.get(paths[1]) is None


class TestCacheStale:
    def test_is_stale_missing(self, cache: HashlineCache, tmp_path: Path) -> None:
        assert cache.is_stale(tmp_path / "nope.py") is True

    def test_is_stale_fresh(self, cache: HashlineCache, tmp_path: Path) -> None:
        p = tmp_path / "fresh.py"
        p.write_text("x", encoding="utf-8")
        cache.put(p, _make_file(p))
        assert cache.is_stale(p) is False

    def test_is_stale_old(self, tmp_path: Path) -> None:
        config = HashlineConfig(stale_threshold_seconds=0.0)
        c = HashlineCache(config)
        p = tmp_path / "old.py"
        p.write_text("x", encoding="utf-8")
        c.put(p, _make_file(p, timestamp=time.time() - 100))
        assert c.is_stale(p) is True


class TestCacheStats:
    def test_stats_tracking(self, cache: HashlineCache, tmp_path: Path) -> None:
        p = tmp_path / "s.py"
        p.write_text("x", encoding="utf-8")

        cache.get(p)  # miss
        cache.put(p, _make_file(p))
        cache.get(p)  # hit

        stats = cache.stats
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.size == 1
        assert stats.evictions == 0


class TestCachePathNormalization:
    def test_relative_and_absolute_same_key(self, cache: HashlineCache, tmp_path: Path) -> None:
        p = tmp_path / "norm.py"
        p.write_text("x", encoding="utf-8")
        cache.put(p, _make_file(p))
        # Use resolved path explicitly
        assert cache.get(p.resolve()) is not None


class TestCacheThreadSafety:
    def test_concurrent_access(self, tmp_path: Path) -> None:
        config = HashlineConfig(cache_max_files=50)
        cache = HashlineCache(config)
        errors: list[str] = []

        def worker(idx: int) -> None:
            try:
                for j in range(20):
                    p = tmp_path / f"thread_{idx}_{j}.py"
                    p.write_text(f"content {idx} {j}", encoding="utf-8")
                    cache.put(p, _make_file(p))
                    cache.get(p)
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
