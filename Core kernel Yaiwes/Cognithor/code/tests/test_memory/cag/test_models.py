from __future__ import annotations

import dataclasses

import pytest

from cognithor.memory.cag.builders import get_builder
from cognithor.memory.cag.models import (
    CacheEntry,
    CAGMetrics,
    CAGRefreshReport,
    CAGStatus,
)

# ---------------------------------------------------------------------------
# CacheEntry
# ---------------------------------------------------------------------------


def _make_entry(**overrides) -> CacheEntry:
    defaults = dict(
        cache_id="core_memory",
        content_hash="abc123",
        normalized_text="hello world",
        token_count=42,
        source_tier="core",
        created_at="2026-04-10T00:00:00Z",
        model_id="qwen3.5:27b",
    )
    defaults.update(overrides)
    return CacheEntry(**defaults)


class TestCacheEntry:
    def test_frozen(self):
        entry = _make_entry()
        with pytest.raises(dataclasses.FrozenInstanceError):
            entry.cache_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CAGMetrics
# ---------------------------------------------------------------------------


class TestCAGMetrics:
    def test_mutable(self):
        m = CAGMetrics()
        m.prefix_hits = 10
        assert m.prefix_hits == 10

    def test_hit_rate(self):
        m = CAGMetrics(prefix_hits=3, prefix_misses=1)
        assert m.hit_rate == pytest.approx(0.75)

    def test_hit_rate_zero(self):
        m = CAGMetrics()
        assert m.hit_rate == 0.0


# ---------------------------------------------------------------------------
# CAGStatus
# ---------------------------------------------------------------------------


class TestCAGStatus:
    def test_frozen(self):
        status = CAGStatus(
            enabled=True,
            backend="prefix",
            entries=[],
            metrics=CAGMetrics(),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            status.enabled = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CAGRefreshReport
# ---------------------------------------------------------------------------


class TestCAGRefreshReport:
    def test_frozen(self):
        report = CAGRefreshReport(refreshed=[], unchanged=[], failed=[])
        with pytest.raises(dataclasses.FrozenInstanceError):
            report.refreshed = ["x"]  # type: ignore[misc]


# ---------------------------------------------------------------------------
# get_builder factory
# ---------------------------------------------------------------------------


class TestGetBuilder:
    def test_auto_returns_prefix(self):
        from cognithor.memory.cag.builders.prefix import PrefixCacheBuilder

        builder = get_builder("auto")
        assert isinstance(builder, PrefixCacheBuilder)

    def test_prefix_returns_prefix(self):
        from cognithor.memory.cag.builders.prefix import PrefixCacheBuilder

        builder = get_builder("prefix")
        assert isinstance(builder, PrefixCacheBuilder)

    def test_llamacpp_native_returns_native(self):
        from cognithor.memory.cag.builders.native import NativeLlamaCppBuilder

        builder = get_builder("llamacpp_native")
        assert isinstance(builder, NativeLlamaCppBuilder)

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown CAG backend"):
            get_builder("unknown")
