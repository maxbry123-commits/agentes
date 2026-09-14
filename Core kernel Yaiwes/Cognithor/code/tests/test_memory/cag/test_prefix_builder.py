from __future__ import annotations

import pytest

from cognithor.memory.cag.builders.prefix import PrefixCacheBuilder
from cognithor.memory.cag.models import CacheEntry


def _entry(cache_id: str = "core", text: str = "hello") -> CacheEntry:
    return CacheEntry(
        cache_id=cache_id,
        content_hash="h",
        normalized_text=text,
        token_count=1,
        source_tier="core",
        created_at="2026-01-01T00:00:00Z",
        model_id="test",
    )


class TestPrefixCacheBuilder:
    @pytest.mark.asyncio
    async def test_prepare_prefix_format(self):
        b = PrefixCacheBuilder()
        result = await b.prepare_prefix([_entry("mem", "data")], "m")
        assert result == "[CAG:mem]\ndata"

    @pytest.mark.asyncio
    async def test_sorted_by_cache_id(self):
        b = PrefixCacheBuilder()
        result = await b.prepare_prefix([_entry("z_last", "z"), _entry("a_first", "a")], "m")
        assert result.index("[CAG:a_first]") < result.index("[CAG:z_last]")

    @pytest.mark.asyncio
    async def test_multiple_entries(self):
        b = PrefixCacheBuilder()
        result = await b.prepare_prefix([_entry("b", "bb"), _entry("a", "aa")], "m")
        assert result == "[CAG:a]\naa\n\n[CAG:b]\nbb"

    @pytest.mark.asyncio
    async def test_empty_entries(self):
        b = PrefixCacheBuilder()
        assert await b.prepare_prefix([], "m") == ""

    @pytest.mark.asyncio
    async def test_is_available(self):
        assert await PrefixCacheBuilder().is_available() is True

    def test_supports_native_state(self):
        assert PrefixCacheBuilder().supports_native_state() is False

    @pytest.mark.asyncio
    async def test_deterministic(self):
        b = PrefixCacheBuilder()
        entries = [_entry("x", "data1"), _entry("y", "data2")]
        r1 = await b.prepare_prefix(entries, "m")
        r2 = await b.prepare_prefix(entries, "m")
        assert r1 == r2
