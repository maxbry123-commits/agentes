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


class TestIntegration:
    async def test_end_to_end(self, manager):
        """build -> get_prefix -> returns non-empty string."""
        report = await manager.build_all(SAMPLE_CORE, MODEL_ID)
        assert len(report.refreshed) > 0

        prefix = await manager.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        assert prefix is not None
        assert len(prefix) > 0

    async def test_prefix_content(self, manager):
        """Prefix contains [CAG:core_memory] header."""
        prefix = await manager.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        assert prefix is not None
        assert "[CAG:core_memory]" in prefix
        # Actual content should appear in the prefix
        assert "Alexander" in prefix

    async def test_fallback_without_cag(self):
        """When cag_prefix is None, planner should use core_memory_text."""
        from cognithor.models import WorkingMemory

        wm = WorkingMemory()
        wm.core_memory_text = "some core memory"
        assert wm.cag_prefix is None

        # Simulate planner logic: cag_prefix takes precedence
        if getattr(wm, "cag_prefix", None):
            used = wm.cag_prefix
        elif wm.core_memory_text:
            used = f"Dein Hintergrund:\n{wm.core_memory_text[:500]}"
        else:
            used = None

        assert used is not None
        assert "Dein Hintergrund" in used
        assert "some core memory" in used

    async def test_metrics_tracked(self, manager):
        """After calls, metrics show correct hit/miss counts."""
        # First call: miss (no previous hash)
        await manager.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        m1 = await manager.get_metrics()
        assert m1.prefix_misses == 1
        assert m1.total_builds >= 1

        # Second call same content: hit
        await manager.get_stable_prefix(SAMPLE_CORE, MODEL_ID)
        m2 = await manager.get_metrics()
        assert m2.prefix_hits == 1
        assert m2.prefix_misses == 1
