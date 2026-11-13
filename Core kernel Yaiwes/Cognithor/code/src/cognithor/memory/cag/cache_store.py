from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from cognithor.memory.cag.models import CacheEntry

if TYPE_CHECKING:
    from pathlib import Path


class CacheStore:
    """Filesystem-backed cache store for CAG entries."""

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, entry: CacheEntry) -> None:
        """Atomically persist a CacheEntry as JSON + a .txt sidecar."""
        data = {
            "cache_id": entry.cache_id,
            "content_hash": entry.content_hash,
            "normalized_text": entry.normalized_text,
            "token_count": entry.token_count,
            "source_tier": entry.source_tier,
            "created_at": entry.created_at,
            "model_id": entry.model_id,
        }
        json_path = self._dir / f"{entry.cache_id}.json"
        tmp_path = self._dir / f"{entry.cache_id}.json.tmp"
        tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(str(tmp_path), str(json_path))

        txt_path = self._dir / f"{entry.cache_id}.txt"
        txt_path.write_text(entry.normalized_text, encoding="utf-8")

    def load(self, cache_id: str) -> CacheEntry | None:
        """Load a CacheEntry by ID, or return None if missing."""
        json_path = self._dir / f"{cache_id}.json"
        if not json_path.exists():
            return None
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return CacheEntry(**data)

    def delete(self, cache_id: str) -> None:
        """Remove both .json and .txt files for a cache entry."""
        for suffix in (".json", ".txt"):
            path = self._dir / f"{cache_id}{suffix}"
            if path.exists():
                path.unlink()

    def list_entries(self) -> list[CacheEntry]:
        """Return all cached entries."""
        entries: list[CacheEntry] = []
        for json_path in sorted(self._dir.glob("*.json")):
            data = json.loads(json_path.read_text(encoding="utf-8"))
            entries.append(CacheEntry(**data))
        return entries

    def total_size_bytes(self) -> int:
        """Sum of all file sizes in the cache directory."""
        total = 0
        for path in self._dir.iterdir():
            if path.is_file():
                total += path.stat().st_size
        return total
