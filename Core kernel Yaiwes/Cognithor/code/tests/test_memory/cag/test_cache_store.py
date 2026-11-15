from __future__ import annotations

from cognithor.memory.cag.cache_store import CacheStore
from cognithor.memory.cag.models import CacheEntry


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


class TestCacheStore:
    def test_save_and_load(self, tmp_path):
        store = CacheStore(tmp_path / "cache")
        entry = _make_entry()
        store.save(entry)
        loaded = store.load("core_memory")
        assert loaded == entry

    def test_load_nonexistent(self, tmp_path):
        store = CacheStore(tmp_path / "cache")
        assert store.load("nope") is None

    def test_delete(self, tmp_path):
        store = CacheStore(tmp_path / "cache")
        store.save(_make_entry())
        store.delete("core_memory")
        assert store.load("core_memory") is None
        assert not (tmp_path / "cache" / "core_memory.txt").exists()

    def test_list_entries(self, tmp_path):
        store = CacheStore(tmp_path / "cache")
        store.save(_make_entry(cache_id="a"))
        store.save(_make_entry(cache_id="b"))
        entries = store.list_entries()
        assert len(entries) == 2
        assert {e.cache_id for e in entries} == {"a", "b"}

    def test_total_size_bytes(self, tmp_path):
        store = CacheStore(tmp_path / "cache")
        store.save(_make_entry())
        assert store.total_size_bytes() > 0

    def test_txt_sidecar_created(self, tmp_path):
        store = CacheStore(tmp_path / "cache")
        store.save(_make_entry())
        txt = tmp_path / "cache" / "core_memory.txt"
        assert txt.exists()
        assert txt.read_text(encoding="utf-8") == "hello world"
