from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional


class MemoryPort:
    def search(self, query, scope=None):
        raise NotImplementedError

    def store(self, item, scope=None):
        raise NotImplementedError

    def context(self, task, scope=None):
        raise NotImplementedError

    def audit(self, item):
        raise NotImplementedError


class PersistentMemory(MemoryPort):
    """Local append-only memory. Production path uses IntelligenceGateway → Router."""

    def __init__(self, root="state/memory"):
        self.path = Path(root) / "memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def store(self, item, scope=None):
        row = {"time": time.time(), "scope": scope, "item": item}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row

    def search(self, query, scope=None):
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if scope and row["scope"] != scope:
                continue
            if query.lower() in json.dumps(row).lower():
                out.append(row)
        return out[-50:]

    def context(self, task, scope=None):
        return self.search(str(task), scope)

    def audit(self, item):
        return {"duplicate": False, "conflict": False, "stale": False, "item": item}

    def update(self, old, new, scope=None):
        return self.store({"update_from": old, "update_to": new}, scope)

    def forget(self, query, scope=None):
        return self.store({"forget": query}, scope)


class MemoryGateway:
    """T19: kv get/set. Optional JSON persist. No Qdrant/LLM."""

    def __init__(self, path: Optional[Path] = None):
        self._data: dict[str, Any] = {}
        self.path = Path(path) if path is not None else None
        if self.path is not None and self.path.is_file():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data = raw

    def _flush(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def set(self, k: str, v: Any) -> Any:
        self._data[str(k)] = v
        self._flush()
        return v

    def get(self, k: str, default: Any = None) -> Any:
        return self._data.get(str(k), default)


if __name__ == "__main__":
    import tempfile

    gw = MemoryGateway()
    gw.set("k", "v")
    assert gw.get("k") == "v"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "kv.json"
        a = MemoryGateway(p)
        a.set("x", 1)
        b = MemoryGateway(p)
        assert b.get("x") == 1
    print("ok", gw.get("k"))
