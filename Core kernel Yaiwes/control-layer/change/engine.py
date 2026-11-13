"""W06 · Change Engine · doc/corrección → impact → DAG patch (sin rebuild)."""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, List


class ChangeType(str, Enum):
    DOCUMENT = "document"
    CORRECTION = "correction"
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    INSTRUCTION = "instruction"
    HERMES_FINDING = "hermes_finding"


@dataclass
class ChangeRequest:
    change_id: str
    type: ChangeType
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    mission_id: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["type"] = self.type.value
        return d


@dataclass
class ImpactReport:
    affected_nodes: list[str]
    severity: str  # low|mid|high
    requires_replan: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DagPatch:
    patch_id: str
    add_nodes: list[str] = field(default_factory=list)
    remove_nodes: list[str] = field(default_factory=list)
    touch_nodes: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_impact(req: ChangeRequest, *, active_nodes: list[str] | None = None) -> ImpactReport:
    nodes = list(active_nodes or [])
    reasons: list[str] = []
    affected: list[str] = []
    severity = "low"
    replan = False

    if req.type == ChangeType.ARCHITECTURE:
        severity = "high"
        replan = True
        affected = nodes or ["architect", "plan", "build"]
        reasons.append("architecture_change")
    elif req.type == ChangeType.CORRECTION:
        severity = "mid"
        affected = [n for n in nodes if n in ("build", "test", "repair")] or ["repair"]
        reasons.append("correction_current_work")
    elif req.type == ChangeType.DOCUMENT:
        severity = "mid"
        affected = [n for n in nodes if n in ("research", "architect", "plan")] or ["plan"]
        reasons.append("document_added")
    elif req.type == ChangeType.REQUIREMENT:
        severity = "high"
        replan = True
        affected = nodes or ["goals", "plan"]
        reasons.append("requirement_change")
    else:
        severity = "low"
        affected = ["plan"]
        reasons.append("instruction_or_finding")

    return ImpactReport(affected_nodes=affected, severity=severity, requires_replan=replan, reasons=reasons)


def build_patch(req: ChangeRequest, impact: ImpactReport) -> DagPatch:
    return DagPatch(
        patch_id="patch_" + uuid.uuid4().hex[:10],
        touch_nodes=list(impact.affected_nodes),
        add_nodes=["repair"] if req.type == ChangeType.CORRECTION else [],
        notes=f"{req.type.value}:{req.summary[:80]}",
    )


class ChangeEngine:
    def apply(
        self,
        *,
        type: str | ChangeType,
        summary: str,
        payload: dict | None = None,
        mission_id: str = "",
        active_nodes: list[str] | None = None,
    ) -> dict[str, Any]:
        ct = type if isinstance(type, ChangeType) else ChangeType(str(type))
        req = ChangeRequest(
            change_id="chg_" + uuid.uuid4().hex[:10],
            type=ct,
            summary=summary,
            payload=dict(payload or {}),
            mission_id=mission_id,
        )
        impact = analyze_impact(req, active_nodes=active_nodes)
        patch = build_patch(req, impact)
        return {
            "request": req.to_dict(),
            "impact": impact.to_dict(),
            "patch": patch.to_dict(),
            "rebuild_workflow": False,  # nunca rebuild completo
        }
