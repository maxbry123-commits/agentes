"""FORENSIC_CODE_CONTRACT v1.3 — schema ejecutable (Salida 2).
Validación de cierre de code dentro del Wordflow.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from enum import Enum

class GateMode(str, Enum):
    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    OPTIONAL = "OPTIONAL"

@dataclass
class FileLocPolicy:
    preferred_max: int = 800
    review_threshold: int = 800
    refactor_threshold: int = 1000
    critical_threshold: int = 1500
    soft_min: int = 300  # design ref, not hard min

@dataclass
class ClosureCounters:
    gaps: int = 0
    blocking_gaps: int = 0
    broken_connections: int = 0
    unexplained_orphans: int = 0
    unreachable_required_paths: int = 0
    unresolved_dependencies: int = 0
    unverified_paths: int = 0
    unverified_requirements: int = 0
    unverified_claims: int = 0
    pending_fixes: int = 0
    new_gaps_after_fix: int = 0
    unexpected_changes: int = 0

    def all_zero(self) -> bool:
        return all(v == 0 for v in asdict(self).values())

    def blocking_zero(self) -> bool:
        return (
            self.blocking_gaps == 0
            and self.broken_connections == 0
            and self.unresolved_dependencies == 0
            and self.unverified_requirements == 0
            and self.unverified_claims == 0
            and self.pending_fixes == 0
            and self.new_gaps_after_fix == 0
        )

@dataclass
class AuditPasses:
    structure: bool = False
    connectivity: bool = False
    behavior: bool = False
    forensic_closure: bool = False

    def all_complete(self) -> bool:
        return self.structure and self.connectivity and self.behavior and self.forensic_closure

@dataclass
class CoreChecks:
    requirements: bool = False
    scope_diff: bool = False
    implementation: bool = False
    architecture: bool = False
    dependencies: bool = False
    contracts: bool = False
    connectivity: bool = False
    behavior: bool = False
    tests: bool = False
    regression_impact: bool = False
    error_paths: bool = False
    code_quality: bool = False
    repository_truth: bool = False
    evidence: bool = False

    def all_pass(self) -> bool:
        return all(asdict(self).values())

@dataclass
class ForensicCodeContract:
    """Contrato de cierre — único criterio de PASS/CLOSED."""
    version: str = "1.3.0"
    file_loc: FileLocPolicy = field(default_factory=FileLocPolicy)
    core: CoreChecks = field(default_factory=CoreChecks)
    passes: AuditPasses = field(default_factory=AuditPasses)
    closure: ClosureCounters = field(default_factory=ClosureCounters)
    context_verified: bool = False
    handoff_verified: bool = False
    evidence_complete: bool = False
    final_clean_reaudit_passed: bool = False
    claim_is_not_proof: bool = True
    skip_equals_pass: bool = False  # ALWAYS false

    def may_start_programming(self) -> bool:
        return self.context_verified and self.handoff_verified

    def evaluate_pass(self) -> bool:
        if not self.may_start_programming():
            return False
        if self.skip_equals_pass:
            return False  # invariant corrupted
        return (
            self.core.all_pass()
            and self.passes.all_complete()
            and self.closure.blocking_zero()
            and self.evidence_complete
            and self.final_clean_reaudit_passed
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "context_verified": self.context_verified,
            "handoff_verified": self.handoff_verified,
            "core": asdict(self.core),
            "passes": asdict(self.passes),
            "closure": asdict(self.closure),
            "evidence_complete": self.evidence_complete,
            "final_clean_reaudit_passed": self.final_clean_reaudit_passed,
            "verdict": "PASS" if self.evaluate_pass() else "FAIL",
        }


class ForensicContractValidator:
    """Valida estado contra contrato. Solo este path + VerdictAuthority deciden PASS."""

    def __init__(self, contract: Optional[ForensicCodeContract] = None):
        self.contract = contract or ForensicCodeContract()

    def block_if_no_context(self) -> Optional[str]:
        if not self.contract.context_verified:
            return "BLOCK: NO CONTEXT → NO PROGRAMMING / NO AUDIT"
        if not self.contract.handoff_verified:
            return "BLOCK: NO HANDOFF VERIFICADO → NO PROGRAMMING / NO AUDIT VÁLIDA"
        return None

    def validate(self) -> Dict[str, Any]:
        block = self.block_if_no_context()
        if block:
            return {"verdict": "BLOCK", "reason": block, "contract": self.contract.to_dict()}
        ok = self.contract.evaluate_pass()
        return {
            "verdict": "PASS" if ok else "FAIL",
            "contract": self.contract.to_dict(),
            "rule": "LLM claim is not PASS; ForensicContractValidator + VerdictAuthority only",
        }
