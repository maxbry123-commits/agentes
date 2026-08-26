from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal
import hashlib, json, time, uuid

Status = Literal["PASS", "FAIL", "PARTIAL", "HOLD", "GAPS_FOUND"]


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class MissionContract:
    mission_id: str
    workspace_id: str
    goals_in: tuple[str, ...]
    goals_out: tuple[str, ...]
    context_hash: str
    version: int = 1


@dataclass
class Evidence:
    evidence_id: str
    kind: str
    path: str | None = None
    sha: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class Gap:
    gap_id: str
    requirement: str
    status: str
    severity: str
    evidence: list[Evidence] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class AuditReport:
    audit_id: str
    target: str
    revision: str
    status: Status
    claims_checked: int
    matches: int
    partial: int
    missing: int
    contradictions: int
    gaps: list[Gap]
    evidence: list[Evidence]


@dataclass
class TaskSpec:
    task_id: str
    gap_id: str
    objective: str
    target: str
    dependencies: tuple[str, ...] = ()
    acceptance: tuple[str, ...] = ()
    status: str = "PENDING"
    workspace_id: str = ""


@dataclass
class Resource:
    resource_id: str
    kind: str
    source: str
    version: str | None = None
    sha: str | None = None
    license: str | None = None
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceEvent:
    trace_id: str
    mission_id: str
    stage: str
    action: str
    parent_trace: str | None
    input_hash: str
    output_hash: str | None
    resource_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    timestamp: float = field(default_factory=time.time)


@dataclass
class Checkpoint:
    mission_id: str
    stage: str
    state: dict[str, Any]
    state_hash: str
    timestamp: float = field(default_factory=time.time)
