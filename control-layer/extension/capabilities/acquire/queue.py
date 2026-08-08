"""TASK_QUEUE · global mission queue · Phase 0.

Persists under root/queue/. Priority: lower number = higher priority.
Scheduler picks RUNNABLE with satisfied depends_on.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .schema import (
    SCHEMA_VERSION,
    TERMINAL_STATUSES,
    MissionStatus,
    QueueEntry,
    _utcnow,
)


class TaskQueue:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.dir = self.root / "queue"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        safe = mission_id.replace("/", "_").replace("..", "_")
        return self.dir / f"{safe}.json"

    def add(self, entry: QueueEntry) -> QueueEntry:
        entry.updated_at = _utcnow()
        entry.schema_version = SCHEMA_VERSION
        self._write(entry)
        return entry

    def get(self, mission_id: str) -> QueueEntry | None:
        p = self._path(mission_id)
        if not p.is_file():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return QueueEntry.from_dict(data)

    def update_status(
        self,
        mission_id: str,
        status: MissionStatus,
        *,
        next_action: str | None = None,
    ) -> QueueEntry:
        e = self.get(mission_id)
        if e is None:
            raise KeyError(f"mission_not_found:{mission_id}")
        e.status = status
        if next_action is not None:
            e.next_action = next_action
        e.updated_at = _utcnow()
        self._write(e)
        return e

    def list_all(self) -> list[QueueEntry]:
        out: list[QueueEntry] = []
        for p in sorted(self.dir.glob("*.json")):
            try:
                out.append(QueueEntry.from_dict(json.loads(p.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        return out

    def pick_next(self) -> QueueEntry | None:
        """Highest priority RUNNABLE whose depends_on are all terminal DONE."""
        done_ids = {
            e.mission_id
            for e in self.list_all()
            if e.status == "DONE"
        }
        candidates = [
            e
            for e in self.list_all()
            if e.status == "RUNNABLE" and all(d in done_ids for d in e.depends_on)
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda e: (e.priority, e.created_at))
        return candidates[0]

    def mark_running(self, mission_id: str) -> QueueEntry:
        return self.update_status(mission_id, "RUNNING", next_action="execute")

    def mark_terminal(
        self,
        mission_id: str,
        status: MissionStatus,
        *,
        next_action: str = "idle",
    ) -> QueueEntry:
        if status not in TERMINAL_STATUSES:
            raise ValueError(f"not_terminal:{status}")
        return self.update_status(mission_id, status, next_action=next_action)

    def enqueue(
        self,
        mission_id: str,
        *,
        repo: str = "",
        tag: str | None = None,
        commit: str | None = None,
        priority: int = 100,
        depends_on: Iterable[str] | None = None,
        dry_run: bool = False,
        status: MissionStatus = "QUEUED",
    ) -> QueueEntry:
        entry = QueueEntry(
            mission_id=mission_id,
            priority=priority,
            status=status,
            depends_on=list(depends_on or []),
            next_action="plan" if not dry_run else "investigate",
            repo=repo,
            tag=tag,
            commit=commit,
            dry_run=dry_run,
        )
        return self.add(entry)

    def promote_queued(self) -> list[str]:
        """QUEUED → RUNNABLE when dependencies DONE."""
        done_ids = {e.mission_id for e in self.list_all() if e.status == "DONE"}
        promoted: list[str] = []
        for e in self.list_all():
            if e.status != "QUEUED":
                continue
            if all(d in done_ids for d in e.depends_on):
                self.update_status(e.mission_id, "RUNNABLE", next_action=e.next_action or "plan")
                promoted.append(e.mission_id)
        return promoted

    def _write(self, entry: QueueEntry) -> None:
        p = self._path(entry.mission_id)
        tmp = p.with_suffix(".json.tmp")
        payload = json.dumps(entry.to_dict(), indent=2, sort_keys=True)
        tmp.write_text(payload + "\n", encoding="utf-8")
        tmp.replace(p)
