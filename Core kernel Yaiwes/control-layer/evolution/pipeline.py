"""Evolution pipeline."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Protocol

from .sandbox_gate import GateDecision, GateReport, SandboxGate
from .source_reuse import SourceReuseContract, SourceReuseDecision


class EvolutionPhase(str, Enum):
    DISCOVERY = "DISCOVERY"
    INVENTORY = "INVENTORY"
    DISTILL = "DISTILL"
    TEMPLATE = "TEMPLATE"
    COMPILE = "COMPILE"
    TEST = "TEST"
    SECURITY = "SECURITY"
    CANARY = "CANARY"
    REGISTRY = "REGISTRY"
    BLOCKED = "BLOCKED"
    DONE = "DONE"


class EvolutionMode(str, Enum):
    AGENT_ABSORB = "agent_absorb"
    DECAPITATE = "decapitate"
    SKILL_COMPILE = "skill_compile"
    OS_SOURCE = "os_source"
    DATASET = "dataset"


@dataclass
class EvolutionRequest:
    mode: EvolutionMode
    source_hint: str
    capability_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    force_scratch_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        return d


@dataclass
class EvolutionResult:
    ok: bool
    phase: EvolutionPhase
    capability_id: str
    mode: str
    package_path: str = ""
    candidate_id: str = ""
    reuse: dict[str, Any] = field(default_factory=dict)
    gate: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value
        return d


class ModeHandler(Protocol):
    mode: EvolutionMode

    def run(self, req: EvolutionRequest, reuse: SourceReuseDecision) -> dict[str, Any]:
        ...


class EvolutionPipeline:
    def __init__(self, **kwargs: Any) -> None:
        self.reuse: SourceReuseContract = kwargs.get("reuse") or SourceReuseContract()
        self.gate: SandboxGate = kwargs.get("gate") or SandboxGate()
        self.handlers: dict[EvolutionMode, ModeHandler] = kwargs.get("handlers") or {}

    def register_handler(self, handler: ModeHandler) -> None:
        self.handlers[handler.mode] = handler

    def run(
        self,
        req: EvolutionRequest,
        *,
        tests_passed: bool = False,
        security_ok: bool = False,
        regression_ok: bool = False,
        canary_ok: bool = False,
        trust_score: float = 0.0,
    ) -> EvolutionResult:
        decision = self.reuse.decide(
            req.source_hint or req.capability_id,
            force_scratch_reason=req.force_scratch_reason,
        )
        if not decision.sources_found and not decision.allow_from_scratch:
            return EvolutionResult(
                False, EvolutionPhase.BLOCKED, req.capability_id, req.mode.value,
                reuse=decision.to_dict(), error="source_reuse_blocked_no_os_source",
            )
        handler = self.handlers.get(req.mode)
        if handler is None:
            return EvolutionResult(
                False, EvolutionPhase.BLOCKED, req.capability_id, req.mode.value,
                reuse=decision.to_dict(), error=f"no_handler_for_mode:{req.mode.value}",
            )
        try:
            out = handler.run(req, decision)
        except Exception as e:
            return EvolutionResult(
                False, EvolutionPhase.BLOCKED, req.capability_id, req.mode.value,
                reuse=decision.to_dict(), error=str(e),
            )
        candidate_id = str(out.get("candidate_id") or f"cand_{req.capability_id}")
        report: GateReport = self.gate.evaluate(
            candidate_id=candidate_id,
            tests_passed=tests_passed,
            security_ok=security_ok,
            regression_ok=regression_ok,
            canary_ok=canary_ok,
            trust_score=trust_score,
        )
        if report.decision == GateDecision.REJECT:
            phase, ok = EvolutionPhase.BLOCKED, False
        elif report.decision == GateDecision.CANARY:
            phase, ok = EvolutionPhase.CANARY, True
        elif report.decision == GateDecision.PROMOTE:
            phase, ok = EvolutionPhase.REGISTRY, True
        else:
            phase, ok = EvolutionPhase.COMPILE, True
        return EvolutionResult(
            ok, phase, req.capability_id, req.mode.value,
            package_path=str(out.get("package_path") or ""),
            candidate_id=candidate_id,
            reuse=decision.to_dict(),
            gate=report.to_dict(),
            evidence=dict(out.get("evidence") or {}),
            error="" if ok else ";".join(report.reasons),
        )
