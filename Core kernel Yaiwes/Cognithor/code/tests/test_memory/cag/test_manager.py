from __future__ import annotations

from dataclasses import dataclass

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


# >50 words so the selector actually returns candidates
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


class TestCAGManager:
    async def test_build_all_creates_entries(self, manager):
        report = await manager.build_all(SAMPLE_CORE, MODEL_ID)
        assert "core_memory" in report.refreshed
        assert len(report.unchanged) == 0
        assert len(report.failed) == 0

    async def test_build_all_skips_unchanged(self, manager):
        await manager.build_all(SAMPLE_CORE, MODEL_ID)
        report2 = await manager.build_all(SAMPLE_CORE, MODEL_ID)
        assert "core_memory" in report2.unchanged
        assert len(report2.refreshed) == 0

    async def test_build_all_rebuilds_changed(self, manager):
        await manager.build_all(SAMPLE_CORE, MODEL_ID)
        report2 = await manager.build_all(SAMPLE_CORE_ALT, MODEL_ID)
        assert "core_memory" in report2.refreshed
        assert len(report2.unchanged) == 0

    async def test_get_stable_prefix_returns_text(self, manager):
        prefix = await manager.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        assert prefix is not None
        assert len(prefix) > 0
        assert "[CAG:core_memory]" in prefix

    async def test_get_stable_prefix_hit(self, manager):
        await manager.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        await manager.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        metrics = await manager.get_metrics()
        assert metrics.prefix_hits >= 1

    async def test_get_stable_prefix_miss(self, manager):
        await manager.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        await manager.get_stable_prefix(SAMPLE_CORE_ALT, MODEL_ID)
        metrics = await manager.get_metrics()
        assert metrics.prefix_misses >= 2  # first call + changed content

    async def test_invalidate(self, manager):
        await manager.build_all(SAMPLE_CORE, MODEL_ID)
        await manager.invalidate("core_memory")
        status = await manager.get_status()
        assert len(status.entries) == 0

    async def test_get_status(self, manager):
        await manager.build_all(SAMPLE_CORE, MODEL_ID)
        status = await manager.get_status()
        assert status.enabled is True
        assert status.backend == "prefix"
        assert len(status.entries) == 1
        assert status.entries[0].cache_id == "core_memory"

    async def test_is_active(self, manager, tmp_path):
        assert manager.is_active is True

        disabled_cfg = _FakeCAGConfig(enabled=False)
        disabled_mgr = CAGManager(
            config=disabled_cfg,
            cache_store=CacheStore(tmp_path / "cag2"),
            builder=PrefixCacheBuilder(),
            selector=CAGSelector(),
            metrics_collector=CAGMetricsCollector(),
        )
        assert disabled_mgr.is_active is False
