"""FORENSIC PROGRAMMING ENFORCEMENT — CORE 01-14 + FC + 4-pass + fail-closed.
Sin bypass de gates REQUIRED. CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from enum import Enum

class PassName(str, Enum):
    STRUCTURE = "STRUCTURE"
    CONNECTIVITY = "CONNECTIVITY"
    BEHAVIOR = "BEHAVIOR"
    FORENSIC_CLOSURE = "FORENSIC_CLOSURE"

CORE_IDS = [
    "CORE-01",  # REQUIREMENT CLOSURE
    "CORE-02",  # SCOPE/DIFF CLOSURE
    "CORE-03",  # IMPLEMENTATION CLOSURE
    "CORE-04",  # ARCHITECTURE/BOUNDARY
    "CORE-05",  # DEPENDENCY CLOSURE
    "CORE-06",  # CONTRACT CLOSURE
    "CORE-07",  # REAL WIRING
    "CORE-08",  # BEHAVIOR/EDGE
    "CORE-09",  # TEST EFFECTIVENESS
    "CORE-10",  # REGRESSION/IMPACT
    "CORE-11",  # ERROR PATH CLOSURE
    "CORE-12",  # CODE QUALITY
    "CORE-13",  # REPOSITORY TRUTH
    "CORE-14",  # EVIDENCE/VERDICT
]

FC_IDS = [f"FC-{i:02d}" for i in range(1, 14)]

# GR-04 — criterios explícitos (caller/CI marca bool con evidencia externa)
FC_CRITERIA: Dict[str, str] = {
    "FC-01": "FILE_LOC within policy thresholds",
    "FC-02": "NO_CIRCULAR_DEPENDENCIES",
    "FC-03": "NO_FORBIDDEN_IMPORTS",
    "FC-04": "DOMAIN_BOUNDARIES respected",
    "FC-05": "PORTS_ADAPTERS where required",
    "FC-06": "CONTRACTS_VERSIONED",
    "FC-07": "CRITICAL_PATHS_VERIFIED",
    "FC-08": "AGENT_RUNTIME_AUTHORITY enforced",
    "FC-09": "NO_DEFAULT_PROD credentials",
    "FC-10": "DETERMINISTIC_FIRST on code path",
    "FC-11": "STATE_OWNERSHIP clear",
    "FC-12": "CI_FAIL_CLOSED skip!=pass",
    "FC-13": "SYMBOL_CONSUMERS_TESTS impact checked",
}

CONNECTIVITY_CHAIN = [
    "DECLARED",
    "REGISTERED",
    "RESOLVED",
    "INVOKED",
    "EXECUTED",
    "OUTPUT_CONSUMED",
    "BEHAVIOR_VERIFIED",
]

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

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)

@dataclass
class CoreCheckResult:
    core_id: str
    passed: bool
    evidence: str = ""
    detail: str = ""

@dataclass
class PassResult:
    name: PassName
    passed: bool
    findings: List[str] = field(default_factory=list)
    evidence: str = ""

@dataclass
class ForensicEnforcementState:
    context_verified: bool = False
    handoff_verified: bool = False
    core_results: List[CoreCheckResult] = field(default_factory=list)
    fc_results: Dict[str, bool] = field(default_factory=dict)
    require_fc: bool = False
    passes: List[PassResult] = field(default_factory=list)
    connectivity: Dict[str, bool] = field(default_factory=dict)
    counters: ClosureCounters = field(default_factory=ClosureCounters)
    evidence_complete: bool = False
    final_clean_reaudit_passed: bool = False
    quality_dag_ok: bool = False
    deterministic_first_ok: bool = True
    claim_used_as_pass: bool = False

    def core_all_pass(self) -> bool:
        if len(self.core_results) < 14:
            return False
        return all(c.passed for c in self.core_results)

    def four_passes_ok(self) -> bool:
        if len(self.passes) < 4:
            return False
        return all(p.passed for p in self.passes)

    def connectivity_ok(self) -> bool:
        return all(self.connectivity.get(k, False) for k in CONNECTIVITY_CHAIN)

    def fc_ok(self) -> bool:
        if not self.require_fc and not self.fc_results:
            return True
        return all(self.fc_results.get(fid, False) for fid in FC_IDS)


class ForensicProgrammingEnforcer:
    """Fail-closed. REQUIRED no se salta. PASS solo con verification+evidence."""

    RULES = {
        "claim_is_not_evidence": True,
        "evidence_is_not_verification": True,
        "verification_plus_evidence_for_pass": True,
        "required_without_handler": "FAIL",
        "required_skip": "FAIL",
        "optional_skip": "ALLOW",
        "skip_equals_pass": False,
        "open_to_closed_forbidden": True,
        "all_four_passes_required": True,
        "no_dev_bypass_required": True,
        "fc_criteria": FC_CRITERIA,
    }

    def require_context(self, context_verified: bool, handoff_verified: bool) -> Optional[str]:
        if not context_verified:
            return "BLOCK: NO VERIFIED CONTEXT → NO PROGRAMMING / NO AUDIT"
        if not handoff_verified:
            return "BLOCK: NO VERIFIED HANDOFF → NO PROGRAMMING / NO AUDIT"
        return None

    def run_four_passes(self, state: ForensicEnforcementState) -> List[PassResult]:
        results: List[PassResult] = []
        struct_ok = all(
            c.passed for c in state.core_results if c.core_id in {"CORE-01", "CORE-02", "CORE-03", "CORE-04", "CORE-05", "CORE-06", "CORE-13"}
        ) if state.core_results else False
        results.append(PassResult(PassName.STRUCTURE, struct_ok, [] if struct_ok else ["structure cores failed"], "core_subset"))
        if not struct_ok:
            results.append(PassResult(PassName.CONNECTIVITY, False, ["blocked by PASS1"], ""))
            results.append(PassResult(PassName.BEHAVIOR, False, ["blocked by PASS1"], ""))
            results.append(PassResult(PassName.FORENSIC_CLOSURE, False, ["blocked by PASS1"], ""))
            return results

        conn_ok = state.connectivity_ok() and any(c.core_id == "CORE-07" and c.passed for c in state.core_results)
        results.append(PassResult(PassName.CONNECTIVITY, conn_ok, [] if conn_ok else ["connectivity chain incomplete"], "chain"))
        if not conn_ok:
            results.append(PassResult(PassName.BEHAVIOR, False, ["blocked by PASS2"], ""))
            results.append(PassResult(PassName.FORENSIC_CLOSURE, False, ["blocked by PASS2"], ""))
            return results

        beh_ok = all(
            c.passed for c in state.core_results if c.core_id in {"CORE-08", "CORE-09", "CORE-10", "CORE-11"}
        )
        results.append(PassResult(PassName.BEHAVIOR, beh_ok, [] if beh_ok else ["behavior cores failed"], "core_subset"))
        if not beh_ok:
            results.append(PassResult(PassName.FORENSIC_CLOSURE, False, ["blocked by PASS3"], ""))
            return results

        clos_ok = (
            state.counters.all_zero()
            and state.evidence_complete
            and state.final_clean_reaudit_passed
            and not state.claim_used_as_pass
            and any(c.core_id == "CORE-14" and c.passed for c in state.core_results)
        )
        results.append(PassResult(PassName.FORENSIC_CLOSURE, clos_ok, [] if clos_ok else ["closure counters or evidence"], "counters+evidence"))
        return results

    def evaluate(self, state: ForensicEnforcementState) -> Dict[str, Any]:
        block = self.require_context(state.context_verified, state.handoff_verified)
        if block:
            return {"verdict": "BLOCK", "reason": block, "rules": self.RULES}

        if state.claim_used_as_pass:
            return {"verdict": "FAIL", "reason": "CLAIM→PASS forbidden", "rules": self.RULES}

        if len(state.core_results) < 14:
            return {
                "verdict": "FAIL",
                "reason": "required_without_handler: CORE 01-14 incomplete",
                "rules": self.RULES,
            }

        # GR-04: FC enforce when require_fc or any fc_results provided
        if state.require_fc or state.fc_results:
            missing = [fid for fid in FC_IDS if not state.fc_results.get(fid, False)]
            if missing:
                return {
                    "verdict": "FAIL",
                    "reason": "FC criteria failed",
                    "fc_failed": missing,
                    "fc_criteria": {m: FC_CRITERIA.get(m, "") for m in missing},
                    "rules": self.RULES,
                }

        state.passes = self.run_four_passes(state)

        if not state.core_all_pass():
            return {"verdict": "FAIL", "reason": "CORE check failed", "passes": [asdict(p) for p in state.passes], "counters": state.counters.to_dict()}

        if not state.four_passes_ok():
            return {"verdict": "FAIL", "reason": "all_four_passes_required", "passes": [asdict(p) for p in state.passes], "counters": state.counters.to_dict()}

        if not state.counters.all_zero():
            return {"verdict": "FAIL", "reason": "closure counters non-zero", "counters": state.counters.to_dict()}

        if not state.evidence_complete or not state.final_clean_reaudit_passed:
            return {"verdict": "FAIL", "reason": "evidence or final_clean_reaudit failed"}

        if not state.quality_dag_ok:
            return {"verdict": "FAIL", "reason": "QualityDAG required gates not pass / skip!=pass"}

        return {
            "verdict": "PASS",
            "reason": "context + CORE14 + FC + 4 passes + counters0 + evidence + final_reaudit",
            "passes": [asdict(p) for p in state.passes],
            "counters": state.counters.to_dict(),
            "rules": self.RULES,
            "connectivity": state.connectivity,
            "fc_ok": state.fc_ok(),
        }
