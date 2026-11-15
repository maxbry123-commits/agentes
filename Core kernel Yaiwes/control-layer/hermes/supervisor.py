"""D02 · Hermes · supervisor/juez · NO ejecuta código de producto."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


class HermesRole(str, Enum):
    SENTINEL = "sentinel"
    JUDGE = "judge"
    SUPERVISOR = "supervisor"
    VALIDATOR = "validator"


class HermesDecision(str, Enum):
    PASS = "PASS"
    FINDING = "FINDING"
    REPAIR = "REPAIR"
    ESCALATE = "ESCALATE"
    BLOCK = "BLOCK"


@dataclass
class HermesReport:
    decision: HermesDecision
    role: HermesRole
    findings: list[str] = field(default_factory=list)
    unmet_goals: list[str] = field(default_factory=list)
    suggested_patch_nodes: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["decision"] = self.decision.value
        d["role"] = self.role.value
        return d


class HermesSupervisor:
    """Audita resultados vs goals/contracts. No llama agentes de código."""

    def audit(
        self,
        *,
        goals_out: Mapping[str, Any] | None,
        output: Mapping[str, Any] | None,
        failures: list[dict[str, Any]] | None = None,
    ) -> HermesReport:
        findings: list[str] = []
        unmet: list[str] = []
        gout = dict(goals_out or {})
        out = dict(output or {})

        for k in ("O01_objetivo_cumplido", "O09_evidencia", "O10_aprobacion_final"):
            if not str(gout.get(k) or "").strip():
                unmet.append(k)

        if not out.get("result") and not out.get("evidence"):
            findings.append("empty_result_or_evidence")

        for f in failures or []:
            if f.get("retryable") is False:
                findings.append(f"hard_failure:{f.get('type')}")

        if unmet:
            return HermesReport(
                decision=HermesDecision.BLOCK,
                role=HermesRole.JUDGE,
                findings=findings,
                unmet_goals=unmet,
                suggested_patch_nodes=["goals", "verify"],
                evidence={"goals_out": gout},
            )
        if findings:
            return HermesReport(
                decision=HermesDecision.FINDING,
                role=HermesRole.VALIDATOR,
                findings=findings,
                suggested_patch_nodes=["repair"],
                evidence={"failures": failures or []},
            )
        return HermesReport(
            decision=HermesDecision.PASS,
            role=HermesRole.SUPERVISOR,
            evidence={"ok": True},
        )
