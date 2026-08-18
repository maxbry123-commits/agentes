"""ChecklistSheriff — juez determinista: sin checklist verificada el agente NO pasa.

El agente debe enviar AgentChecklistClaim con puntos considerados + evidencia mínima.
El sheriff no ejecuta 500 herramientas: verifica cobertura de puntos REQUIRED y claims.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Set
from .programming_points_catalog import (
    PROGRAMMING_POINTS,
    BY_ID,
    required_ids_for_stages,
)

@dataclass
class PointClaim:
    point_id: str
    addressed: bool
    evidence: str = ""  # path, note, measure key — no vacío si required
    skipped_reason: str = ""  # solo si not required

@dataclass
class AgentChecklistClaim:
    mission_id: str
    task_id: str
    stages: List[str] = field(default_factory=lambda: ["context", "plan", "copy", "apply", "verify", "verdict"])
    claims: List[PointClaim] = field(default_factory=list)
    action: str = "GENERATE"  # COPY|ADAPT|GENERATE
    sources: List[str] = field(default_factory=list)
    files_touched: List[str] = field(default_factory=list)

@dataclass
class SheriffFinding:
    point_id: str
    severity: str  # BLOCK|WARN
    message: str

@dataclass
class SheriffVerdict:
    passed: bool
    findings: List[SheriffFinding] = field(default_factory=list)
    required_total: int = 0
    required_addressed: int = 0
    coverage_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "required_total": self.required_total,
            "required_addressed": self.required_addressed,
            "coverage_ratio": self.coverage_ratio,
            "findings": [asdict(f) for f in self.findings],
        }


class ChecklistSheriff:
    """Sentinel/juez: BLOCK si falta required sin evidence o claims incompletos."""

    def evaluate(self, claim: AgentChecklistClaim) -> SheriffVerdict:
        findings: List[SheriffFinding] = []
        stages = set(claim.stages)
        required = required_ids_for_stages(stages)
        claimed_map = {c.point_id: c for c in claim.claims}

        # Acción COPY/ADAPT exige sources + E088/E147/E489
        if claim.action in ("COPY", "ADAPT"):
            if not claim.sources:
                findings.append(SheriffFinding("E088", "BLOCK", "ADAPT/COPY sin sources"))
            for pid in ("E088", "E147", "E489"):
                if pid in required or True:
                    c = claimed_map.get(pid)
                    if not c or not c.addressed or not c.evidence:
                        findings.append(SheriffFinding(pid, "BLOCK", f"{pid} requiere addressed+evidence en {claim.action}"))

        addressed = 0
        for pid in required:
            c = claimed_map.get(pid)
            if c is None:
                findings.append(SheriffFinding(pid, "BLOCK", f"required {pid} no declarado en checklist"))
                continue
            if not c.addressed:
                if c.skipped_reason and not BY_ID[pid].required_default:
                    continue
                findings.append(SheriffFinding(pid, "BLOCK", f"required {pid} not addressed"))
                continue
            if not (c.evidence or "").strip():
                findings.append(SheriffFinding(pid, "BLOCK", f"required {pid} sin evidence"))
                continue
            addressed += 1

        # GENERATE sin justificar ausencia de match
        if claim.action == "GENERATE":
            c = claimed_map.get("E490")
            if not c or not c.addressed:
                findings.append(SheriffFinding("E490", "BLOCK", "GENERATE sin claim de no-match/hash"))

        # files touched sin allowlist claim
        if claim.files_touched:
            c = claimed_map.get("E101")
            if not c or not c.addressed or not c.evidence:
                findings.append(SheriffFinding("E101", "BLOCK", "files_touched sin allowlist evidence"))

        blocks = [f for f in findings if f.severity == "BLOCK"]
        total = len(required) or 1
        ratio = addressed / total
        return SheriffVerdict(
            passed=len(blocks) == 0,
            findings=findings,
            required_total=len(required),
            required_addressed=addressed,
            coverage_ratio=ratio,
        )
