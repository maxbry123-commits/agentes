from __future__ import annotations

import json
import time
from pathlib import Path


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
