"""Tests für TTLDict — Time-To-Live Dict mit LRU-Eviction."""

from __future__ import annotations

import time

import pytest

from cognithor.utils.ttl_dict import TTLDict

# ============================================================================
# Basic Operations
# ============================================================================


class TestBasicOperations:
    def test_set_and_get(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        d.set("a", 1)
        assert d.get("a") == 1

    def test_setitem_getitem(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        d["x"] = 42
        assert d["x"] == 42

    def test_contains(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        d["k"] = 1
        assert "k" in d
        assert "missing" not in d

    def test_delitem(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        d["k"] = 1
        del d["k"]
        assert "k" not in d

    def test_delitem_missing_raises(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        with pytest.raises(KeyError):
            del d["missing"]

    def test_pop(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        d["k"] = 99
        assert d.pop("k") == 99
        assert "k" not in d

    def test_pop_default(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        assert d.pop("missing", 0) == 0

    def test_pop_missing_raises(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        with pytest.raises(KeyError):
            d.pop("missing")

    def test_len(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        assert len(d) == 0
        d["a"] = 1
        d["b"] = 2
        assert len(d) == 2

    def test_clear(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        d["a"] = 1
        d["b"] = 2
        d.clear()
        assert len(d) == 0

    def test_keys_values_items(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        d["a"] = 1
        d["b"] = 2
        assert set(d.keys()) == {"a", "b"}
        assert set(d.values()) == {1, 2}
        assert set(d.items()) == {("a", 1), ("b", 2)}

    def test_iter(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        d["a"] = 1
        d["b"] = 2
        assert set(d) == {"a", "b"}

    def test_get_default(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        assert d.get("missing") is None
        assert d.get("missing", 42) == 42

    def test_getitem_missing_raises(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60)
        with pytest.raises(KeyError):
            _ = d["missing"]

    def test_repr(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=50, ttl_seconds=30)
        r = repr(d)
        assert "TTLDict" in r
        assert "50" in r


# ============================================================================
# Expiration
# ============================================================================


class TestExpiration:
    def test_expired_get_returns_none(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=1)
        d.set("k", 42)

        # Simuliere Zeitablauf
        entry = d._data["k"]
        entry.expires_at = time.monotonic() - 1

        assert d.get("k") is None

    def test_expired_not_in_contains(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=1)
        d.set("k", 42)

        entry = d._data["k"]
        entry.expires_at = time.monotonic() - 1

        assert "k" not in d

    def test_expired_getitem_raises(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=1)
        d.set("k", 42)

        entry = d._data["k"]
        entry.expires_at = time.monotonic() - 1

        with pytest.raises(KeyError):
            _ = d["k"]

    def test_custom_ttl_per_entry(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=3600)
        d.set("short", 1, ttl=1)
        d.set("long", 2, ttl=7200)

        # short entry verfällt
        d._data["short"].expires_at = time.monotonic() - 1

        assert d.get("short") is None
        assert d.get("long") == 2

    def test_cleanup_removes_expired(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60, cleanup_interval=0)
        d.set("alive", 1)
        d.set("dead", 2)

        d._data["dead"].expires_at = time.monotonic() - 1

        # Trigger cleanup via set (cleanup_interval=0 → immer)
        d.set("trigger", 3)

        assert "dead" not in d._data
        assert "alive" in d._data

    def test_auto_cleanup_on_access(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=60, cleanup_interval=0)
        d.set("dead1", 1)
        d.set("dead2", 2)
        d.set("alive", 3)

        d._data["dead1"].expires_at = time.monotonic() - 1
        d._data["dead2"].expires_at = time.monotonic() - 1

        # get triggert cleanup
        d.get("alive")

        assert len(d._data) == 1


# ============================================================================
# LRU Eviction
# ============================================================================


class TestLRU:
    def test_max_size_evicts_oldest(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=3, ttl_seconds=3600)
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3
        d["d"] = 4  # sollte "a" evicten

        assert "a" not in d._data
        assert len(d) == 3
        assert d["d"] == 4

    def test_access_refreshes_order(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=3, ttl_seconds=3600)
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3

        # Zugriff auf "a" macht es zum neuesten
        _ = d["a"]

        d["d"] = 4  # sollte "b" evicten (ältester Zugriff)

        assert "a" in d._data
        assert "b" not in d._data

    def test_eviction_count_tracked(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=2, ttl_seconds=3600)
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3  # evict "a"
        d["d"] = 4  # evict "b"

        assert d.stats["eviction_count"] == 2


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    def test_zero_ttl_expires_immediately(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=0)
        d.set("k", 42)
        # Monotonic clock Auflösung: Entry expires_at == now, also abgelaufen
        # (>= check in get)
        assert d.get("k") is None

    def test_overwrite_resets_ttl(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=3600)
        d.set("k", 1)
        old_expires = d._data["k"].expires_at

        # Neuen Wert setzen
        d.set("k", 2)
        new_expires = d._data["k"].expires_at

        assert new_expires >= old_expires
        assert d["k"] == 2

    def test_stats_reporting(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=2, ttl_seconds=60)
        d["a"] = 1
        d["b"] = 2

        stats = d.stats
        assert stats["size"] == 2
        assert stats["max_size"] == 2
        assert stats["eviction_count"] == 0
        assert stats["expired_count"] == 0

    def test_expired_count_tracked(self) -> None:
        d: TTLDict[str, int] = TTLDict(max_size=100, ttl_seconds=1)
        d.set("k", 42)
        d._data["k"].expires_at = time.monotonic() - 1

        d.get("k")  # triggers expired removal

        assert d.stats["expired_count"] == 1
