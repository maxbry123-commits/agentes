"""acquire schema · Phase 0 · generic, deterministic types.

No project-specific fields. No network. Pure data contracts.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

SCHEMA_VERSION = "0.1.0-phase0"

# --- status sets ---

TASK_STATUSES = (
    "QUEUED",
    "RUNNABLE",
    "RUNNING",
    "DONE",
    "BLOCKED",
    "FAILED",
    "BUDGET_EXCEEDED",
)

TERMINAL_STATUSES = frozenset({"DONE", "BLOCKED", "FAILED", "BUDGET_EXCEEDED"})

NODE_STATUSES = ("PENDING", "DONE", "FAILED", "SKIPPED", "RETRYABLE")

MissionStatus = Literal[
    "QUEUED", "RUNNABLE", "RUNNING", "DONE", "BLOCKED", "FAILED", "BUDGET_EXCEEDED"
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(payload: dict[str, Any]) -> str:
    """Deterministic content hash (sorted keys, no whitespace noise)."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class StopPolicy:
    max_nodes: int = 64
    max_wall_time_sec: float = 300.0
    max_bytes_downloaded: int = 0  # 0 = no download in phase 0
    max_retries_total: int = 8
    max_api_calls: int = 0
    max_concurrent_operations: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any] | None) -> "StopPolicy":
        d = d or {}
        return StopPolicy(
            max_nodes=int(d.get("max_nodes", 64)),
            max_wall_time_sec=float(d.get("max_wall_time_sec", 300.0)),
            max_bytes_downloaded=int(d.get("max_bytes_downloaded", 0)),
            max_retries_total=int(d.get("max_retries_total", 8)),
            max_api_calls=int(d.get("max_api_calls", 0)),
            max_concurrent_operations=int(d.get("max_concurrent_operations", 1)),
        )


@dataclass
class QueueEntry:
    """TASK_QUEUE global row."""

    mission_id: str
    priority: int = 100
    status: MissionStatus = "QUEUED"
    depends_on: list[str] = field(default_factory=list)
    next_action: str = "plan"
    repo: str = ""
    tag: str | None = None
    commit: str | None = None
    dry_run: bool = False
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "QueueEntry":
        return QueueEntry(
            mission_id=str(d["mission_id"]),
            priority=int(d.get("priority", 100)),
            status=d.get("status", "QUEUED"),  # type: ignore[arg-type]
            depends_on=list(d.get("depends_on") or []),
            next_action=str(d.get("next_action") or "plan"),
            repo=str(d.get("repo") or ""),
            tag=d.get("tag"),
            commit=d.get("commit"),
            dry_run=bool(d.get("dry_run", False)),
            created_at=str(d.get("created_at") or _utcnow()),
            updated_at=str(d.get("updated_at") or _utcnow()),
            schema_version=str(d.get("schema_version") or SCHEMA_VERSION),
        )


@dataclass
class Checkpoint:
    """Transactional resume pointer."""

    mission_id: str
    node_id: str | None = None
    next_offset: int = 0
    next_index: int = 0
    nodes_done: int = 0
    nodes_total: int = 0
    status: MissionStatus = "RUNNABLE"
    schema_version: str = SCHEMA_VERSION
    previous_checkpoint_hash: str | None = None
    checkpoint_hash: str | None = None
    updated_at: str = field(default_factory=_utcnow)
    extra: dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        body = {
            "mission_id": self.mission_id,
            "node_id": self.node_id,
            "next_offset": self.next_offset,
            "next_index": self.next_index,
            "nodes_done": self.nodes_done,
            "nodes_total": self.nodes_total,
            "status": self.status,
            "schema_version": self.schema_version,
            "previous_checkpoint_hash": self.previous_checkpoint_hash,
            "extra": self.extra,
        }
        return stable_hash(body)

    def seal(self) -> "Checkpoint":
        self.updated_at = _utcnow()
        self.checkpoint_hash = self.compute_hash()
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Checkpoint":
        return Checkpoint(
            mission_id=str(d["mission_id"]),
            node_id=d.get("node_id"),
            next_offset=int(d.get("next_offset") or 0),
            next_index=int(d.get("next_index") or 0),
            nodes_done=int(d.get("nodes_done") or 0),
            nodes_total=int(d.get("nodes_total") or 0),
            status=d.get("status", "RUNNABLE"),  # type: ignore[arg-type]
            schema_version=str(d.get("schema_version") or SCHEMA_VERSION),
            previous_checkpoint_hash=d.get("previous_checkpoint_hash"),
            checkpoint_hash=d.get("checkpoint_hash"),
            updated_at=str(d.get("updated_at") or _utcnow()),
            extra=dict(d.get("extra") or {}),
        )


@dataclass
class MemoryOps:
    """Slim operational memory — resume only, never full journal."""

    mission_id: str
    next_action: str = "plan"
    strategy: str | None = None
    last_error: str | None = None
    progress: dict[str, Any] = field(default_factory=dict)
    offset: int = 0
    bytes_downloaded: int = 0
    depends_on: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)
    decisions: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    updated_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "MemoryOps":
        return MemoryOps(
            mission_id=str(d["mission_id"]),
            next_action=str(d.get("next_action") or "plan"),
            strategy=d.get("strategy"),
            last_error=d.get("last_error"),
            progress=dict(d.get("progress") or {}),
            offset=int(d.get("offset") or 0),
            bytes_downloaded=int(d.get("bytes_downloaded") or 0),
            depends_on=list(d.get("depends_on") or []),
            subtasks=list(d.get("subtasks") or []),
            decisions=dict(d.get("decisions") or {}),
            schema_version=str(d.get("schema_version") or SCHEMA_VERSION),
            updated_at=str(d.get("updated_at") or _utcnow()),
        )


@dataclass
class JournalEvent:
    """One append-only journal line."""

    mission_id: str
    op: str
    ok: bool
    node_id: str | None = None
    evidence_hash: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=_utcnow)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "JournalEvent":
        return JournalEvent(
            mission_id=str(d["mission_id"]),
            op=str(d.get("op") or ""),
            ok=bool(d.get("ok", False)),
            node_id=d.get("node_id"),
            evidence_hash=d.get("evidence_hash"),
            detail=dict(d.get("detail") or {}),
            ts=str(d.get("ts") or _utcnow()),
            schema_version=str(d.get("schema_version") or SCHEMA_VERSION),
        )
