"""MEMORY ops · slim resume state · Phase 0.

Only what is needed to continue: next_action, strategy, last_error,
progress, offset, bytes, depends_on, subtasks, decisions.
Never stores full journal. Path: memory/ops/{mission_id}.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import SCHEMA_VERSION, MemoryOps, _utcnow


class MemoryOpsStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.dir = self.root / "memory" / "ops"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        safe = mission_id.replace("/", "_").replace("..", "_")
        return self.dir / f"{safe}.json"

    def get(self, mission_id: str) -> MemoryOps | None:
        p = self._path(mission_id)
        if not p.is_file():
            return None
        try:
            return MemoryOps.from_dict(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def save(self, mem: MemoryOps) -> MemoryOps:
        mem.schema_version = SCHEMA_VERSION
        mem.updated_at = _utcnow()
        p = self._path(mem.mission_id)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(mem.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(p)
        return mem

    def init(self, mission_id: str, *,
             next_action: str = "plan",
             depends_on: list[str] | None = None) -> MemoryOps:
        mem = MemoryOps(
            mission_id=mission_id,
            next_action=next_action,
            depends_on=list(depends_on or []),
            progress={"nodes_done": 0, "nodes_total": 0},
        )
        return self.save(mem)

    def update(
        self,
        mission_id: str,
        *,
        next_action: str | None = None,
        strategy: str | None = None,
        last_error: str | None = None,
        clear_error: bool = False,
        progress: dict[str, Any] | None = None,
        offset: int | None = None,
        bytes_downloaded: int | None = None,
        decisions: dict[str, Any] | None = None,
        subtasks: list[str] | None = None,
    ) -> MemoryOps:
        mem = self.get(mission_id)
        if mem is None:
            mem = MemoryOps(mission_id=mission_id)
        if next_action is not None:
            mem.next_action = next_action
        if strategy is not None:
            mem.strategy = strategy
        if clear_error:
            mem.last_error = None
        elif last_error is not None:
            mem.last_error = last_error
        if progress is not None:
            mem.progress.update(progress)
        if offset is not None:
            mem.offset = offset
        if bytes_downloaded is not None:
            mem.bytes_downloaded = bytes_downloaded
        if decisions is not None:
            mem.decisions.update(decisions)
        if subtasks is not None:
            mem.subtasks = list(subtasks)
        return self.save(mem)

    def exists(self, mission_id: str) -> bool:
        return self._path(mission_id).is_file()
