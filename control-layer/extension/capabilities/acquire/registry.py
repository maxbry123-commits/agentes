"""Mission registry · detailed task record per mission_id · Phase 0.

Stored under root/tasks/{mission_id}.json
Holds full mission detail beyond the slim QUEUE row.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .schema import SCHEMA_VERSION, MissionStatus, StopPolicy, _utcnow


@dataclass
class MissionRecord:
    mission_id: str
    repo: str = ""
    tag: str | None = None
    commit: str | None = None
    dest_root: str | None = None
    priority: int = 100
    status: MissionStatus = "QUEUED"
    depends_on: list[str] = field(default_factory=list)
    next_action: str = "plan"
    dry_run: bool = False
    dag_ref: str | None = None
    checkpoint_ref: str | None = None
    budget: dict[str, Any] = field(default_factory=dict)
    stop_policy: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    schema_version: str = SCHEMA_VERSION
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "MissionRecord":
        return MissionRecord(
            mission_id=str(d["mission_id"]),
            repo=str(d.get("repo") or ""),
            tag=d.get("tag"),
            commit=d.get("commit"),
            dest_root=d.get("dest_root"),
            priority=int(d.get("priority", 100)),
            status=d.get("status", "QUEUED"),  # type: ignore[arg-type]
            depends_on=list(d.get("depends_on") or []),
            next_action=str(d.get("next_action") or "plan"),
            dry_run=bool(d.get("dry_run", False)),
            dag_ref=d.get("dag_ref"),
            checkpoint_ref=d.get("checkpoint_ref"),
            budget=dict(d.get("budget") or {}),
            stop_policy=dict(d.get("stop_policy") or StopPolicy().to_dict()),
            created_at=str(d.get("created_at") or _utcnow()),
            updated_at=str(d.get("updated_at") or _utcnow()),
            schema_version=str(d.get("schema_version") or SCHEMA_VERSION),
            meta=dict(d.get("meta") or {}),
        )


class MissionRegistry:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.dir = self.root / "tasks"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        safe = mission_id.replace("/", "_").replace("..", "_")
        return self.dir / f"{safe}.json"

    def save(self, record: MissionRecord) -> MissionRecord:
        record.updated_at = _utcnow()
        record.schema_version = SCHEMA_VERSION
        p = self._path(record.mission_id)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(p)
        return record

    def get(self, mission_id: str) -> MissionRecord | None:
        p = self._path(mission_id)
        if not p.is_file():
            return None
        return MissionRecord.from_dict(json.loads(p.read_text(encoding="utf-8")))

    def create(
        self,
        mission_id: str,
        *,
        repo: str = "",
        tag: str | None = None,
        commit: str | None = None,
        dest_root: str | None = None,
        priority: int = 100,
        depends_on: list[str] | None = None,
        dry_run: bool = False,
        stop_policy: StopPolicy | None = None,
        meta: dict[str, Any] | None = None,
    ) -> MissionRecord:
        sp = stop_policy or StopPolicy()
        rec = MissionRecord(
            mission_id=mission_id,
            repo=repo,
            tag=tag,
            commit=commit,
            dest_root=dest_root,
            priority=priority,
            status="QUEUED",
            depends_on=list(depends_on or []),
            next_action="investigate" if dry_run else "plan",
            dry_run=dry_run,
            checkpoint_ref=f"checkpoints/{mission_id}.json",
            budget={
                "nodes_used": 0,
                "bytes_downloaded": 0,
                "retries_used": 0,
                "api_calls_used": 0,
            },
            stop_policy=sp.to_dict(),
            meta=dict(meta or {}),
        )
        return self.save(rec)

    def set_status(
        self,
        mission_id: str,
        status: MissionStatus,
        *,
        next_action: str | None = None,
    ) -> MissionRecord:
        rec = self.get(mission_id)
        if rec is None:
            raise KeyError(f"mission_not_found:{mission_id}")
        rec.status = status
        if next_action is not None:
            rec.next_action = next_action
        return self.save(rec)

    def bump_budget(self, mission_id: str, **kwargs: int) -> MissionRecord:
        rec = self.get(mission_id)
        if rec is None:
            raise KeyError(f"mission_not_found:{mission_id}")
        for k, v in kwargs.items():
            rec.budget[k] = int(rec.budget.get(k, 0)) + int(v)
        return self.save(rec)

    def exists(self, mission_id: str) -> bool:
        return self._path(mission_id).is_file()
