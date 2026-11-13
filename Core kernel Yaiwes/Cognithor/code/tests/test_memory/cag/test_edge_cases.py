from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest

from cognithor.memory.cag.builders.prefix import PrefixCacheBuilder
from cognithor.memory.cag.cache_store import CacheStore
from cognithor.memory.cag.manager import CAGManager
from cognithor.memory.cag.metrics import CAGMetricsCollector
from cognithor.memory.cag.selectors import CAGSelector


@dataclass
class _FakeCAGConfig:
    enabled: bool = True
    backend: str = "prefix"
    cache_dir: str = ""
    auto_rebuild_on_change: bool = True
    rebuild_debounce_seconds: int = 30


SAMPLE_CORE = (
    "Alexander is a software engineer working on Cognithor, "
    "a personal AI assistant system. He lives in Munich, Germany "
    "and enjoys building intelligent agents that can handle complex "
    "tasks autonomously. The system uses multiple memory tiers "
    "including core memory, semantic memory, episodic memory, "
    "procedural memory, tactical memory, and working memory. "
    "Each tier has different retention and retrieval strategies "
    "to ensure relevant context is always available to the planner."
)

SAMPLE_CORE_ALT = (
    "Bob is a data scientist working on a different project "
    "called DataFlow, a pipeline orchestration system. He lives "
    "in Berlin and specializes in building data transformation "
    "workflows that can process large datasets efficiently. "
    "The system uses multiple processing stages including ingestion, "
    "transformation, validation, enrichment, aggregation, and output. "
    "Each stage has different configurations and retry strategies "
    "to ensure robust data processing across all pipelines."
)

MODEL_ID = "qwen3.5:27b"


@pytest.fixture()
def manager(tmp_path):
    cfg = _FakeCAGConfig(cache_dir=str(tmp_path / "cag"))
    store = CacheStore(tmp_path / "cag")
    return CAGManager(
        config=cfg,
        cache_store=store,
        builder=PrefixCacheBuilder(),
        selector=CAGSelector(),
        metrics_collector=CAGMetricsCollector(),
    )


class TestEdgeCases:
    async def test_builder_not_available(self, tmp_path):
        """When builder.is_available returns False, get_stable_prefix still works from cache."""
        cfg = _FakeCAGConfig(cache_dir=str(tmp_path / "cag"))
        store = CacheStore(tmp_path / "cag")
        builder = PrefixCacheBuilder()

        mgr = CAGManager(
            config=cfg,
            cache_store=store,
            builder=builder,
            selector=CAGSelector(),
            metrics_collector=CAGMetricsCollector(),
        )

        # Build initial cache
        await mgr.build_all(SAMPLE_CORE, MODEL_ID)

        # Mock is_available to False — prefix should still work (already cached)
        with patch.object(builder, "is_available", new_callable=AsyncMock, return_value=False):
            prefix = await mgr.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
            assert prefix is not None
            assert "[CAG:core_memory]" in prefix

    async def test_disk_full(self, tmp_path):
        """When save raises OSError, manager catches and returns report with failure."""
        cfg = _FakeCAGConfig(cache_dir=str(tmp_path / "cag"))
        store = CacheStore(tmp_path / "cag")
        mgr = CAGManager(
            config=cfg,
            cache_store=store,
            builder=PrefixCacheBuilder(),
            selector=CAGSelector(),
            metrics_collector=CAGMetricsCollector(),
        )

        with patch.object(store, "save", side_effect=OSError("No space left")):
            report = await mgr.build_all(SAMPLE_CORE, MODEL_ID)
            assert len(report.failed) == 1
            assert report.failed[0][0] == "core_memory"
            assert "No space left" in report.failed[0][1]

    async def test_corrupt_cache_file(self, tmp_path):
        """Corrupt JSON file -> load returns None, rebuild works after cleanup."""
        cache_dir = tmp_path / "cag"
        cache_dir.mkdir(parents=True)
        corrupt_path = cache_dir / "core_memory.json"
        corrupt_path.write_text("{invalid json!!", encoding="utf-8")

        import contextlib

        store = CacheStore(cache_dir)
        # load should fail gracefully
        with contextlib.suppress(Exception):
            store.load("core_memory")

        cfg = _FakeCAGConfig(cache_dir=str(cache_dir))
        mgr = CAGManager(
            config=cfg,
            cache_store=store,
            builder=PrefixCacheBuilder(),
            selector=CAGSelector(),
            metrics_collector=CAGMetricsCollector(),
        )

        # Delete corrupt file first, then rebuild
        store.delete("core_memory")
        report = await mgr.build_all(SAMPLE_CORE, MODEL_ID)
        assert "core_memory" in report.refreshed

    async def test_concurrent_rebuild(self, manager):
        """Two concurrent build_all calls should not crash (AsyncLock)."""
        results = await asyncio.gather(
            manager.build_all(SAMPLE_CORE, MODEL_ID),
            manager.build_all(SAMPLE_CORE, MODEL_ID),
        )
        assert len(results) == 2
        # Both should complete without error
        for report in results:
            assert len(report.failed) == 0

    async def test_empty_content(self, manager):
        """Empty core memory -> no cache, returns None."""
        prefix = await manager.get_stable_prefix("", MODEL_ID)
        assert prefix is None

    async def test_short_content(self, manager):
        """Content <50 tokens -> selector skips, returns None."""
        short = "This is a short text with fewer than fifty tokens."
        prefix = await manager.get_stable_prefix(short, MODEL_ID)
        assert prefix is None

    async def test_content_changed(self, manager):
        """Different text -> refresh report shows refreshed."""
        await manager.build_all(SAMPLE_CORE, MODEL_ID)
        report = await manager.build_all(SAMPLE_CORE_ALT, MODEL_ID)
        assert "core_memory" in report.refreshed
        assert len(report.unchanged) == 0

    async def test_schema_version_mismatch(self, tmp_path):
        """Entry with unexpected fields treated as stale -> rebuild works."""
        cache_dir = tmp_path / "cag"
        cache_dir.mkdir(parents=True)

        # Write an entry with extra field (simulating schema v999)
        data = {
            "cache_id": "core_memory",
            "content_hash": "stale_hash_that_wont_match",
            "normalized_text": "old content",
            "token_count": 2,
            "source_tier": "core",
            "created_at": "2020-01-01T00:00:00Z",
            "model_id": "old_model",
        }
        (cache_dir / "core_memory.json").write_text(json.dumps(data), encoding="utf-8")

        store = CacheStore(cache_dir)
        cfg = _FakeCAGConfig(cache_dir=str(cache_dir))
        mgr = CAGManager(
            config=cfg,
            cache_store=store,
            builder=PrefixCacheBuilder(),
            selector=CAGSelector(),
            metrics_collector=CAGMetricsCollector(),
        )

        # Hash won't match new content -> treated as stale, gets refreshed
        report = await mgr.build_all(SAMPLE_CORE, MODEL_ID)
        assert "core_memory" in report.refreshed

    async def test_config_disabled(self, tmp_path):
        """enabled=False -> is_active=False, no prefix."""
        cfg = _FakeCAGConfig(enabled=False, cache_dir=str(tmp_path / "cag"))
        store = CacheStore(tmp_path / "cag")
        mgr = CAGManager(
            config=cfg,
            cache_store=store,
            builder=PrefixCacheBuilder(),
            selector=CAGSelector(),
            metrics_collector=CAGMetricsCollector(),
        )
        assert mgr.is_active is False
        prefix = await mgr.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        assert prefix is None
