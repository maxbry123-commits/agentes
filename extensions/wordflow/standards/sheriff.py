"""StandardSheriff — gates RULE-001..022 (fail-closed en críticos)."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from .schema import StandardContract, RuleId

@dataclass
class Finding:
    rule: RuleId
    severity: str  # P0 | P1 | P2
    message: str
    path: Optional[str] = None

@dataclass
class SheriffVerdict:
    passed: bool
    findings: List[Finding] = field(default_factory=list)

    @property
    def p0(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "P0"]

class StandardSheriff:
    def __init__(self, contract: Optional[StandardContract] = None):
        self.contract = contract or StandardContract()

    def check_file_loc(self, path: Path, loc: int) -> Optional[Finding]:
        if loc > 1500:
            return Finding(RuleId.FILE_LOC, "P0", f"LOC={loc} > 1500 excepción crítica", str(path))
        if loc > 1000:
            return Finding(RuleId.FILE_LOC, "P1", f"LOC={loc} > 1000 candidato refactor", str(path))
        if loc > self.contract.file_loc_preferred_max:
            return Finding(RuleId.FILE_LOC, "P2", f"LOC={loc} > preferred {self.contract.file_loc_preferred_max}", str(path))
        return None

    def check_never_mvp(self, claim_mvp: bool) -> Optional[Finding]:
        if claim_mvp and self.contract.never_mvp:
            return Finding(RuleId.NEVER_MVP, "P0", "Claim MVP prohibido — solo nivel profesional avanzado")
        return None

    def check_gaps_100(self, gaps_open: int) -> Optional[Finding]:
        if gaps_open > 0 and self.contract.gaps_must_be_100:
            return Finding(RuleId.GAPS_100, "P0", f"Gaps abiertos={gaps_open}; deben ser 0 antes de avanzar")
        return None

    def check_ai_not_proof(self, used_ai_as_proof: bool) -> Optional[Finding]:
        if used_ai_as_proof and self.contract.ai_output_is_not_proof:
            return Finding(RuleId.AI_NOT_PROOF, "P0", "AI output no es prueba de corrección")
        return None

    def evaluate(
        self,
        *,
        file_locs: Optional[Dict[str, int]] = None,
        claim_mvp: bool = False,
        gaps_open: int = 0,
        used_ai_as_proof: bool = False,
    ) -> SheriffVerdict:
        findings: List[Finding] = []
        for p, loc in (file_locs or {}).items():
            f = self.check_file_loc(Path(p), loc)
            if f:
                findings.append(f)
        for checker, arg in (
            (self.check_never_mvp, claim_mvp),
            (self.check_gaps_100, gaps_open),
            (self.check_ai_not_proof, used_ai_as_proof),
        ):
            f = checker(arg)
            if f:
                findings.append(f)
        p0 = [f for f in findings if f.severity == "P0"]
        return SheriffVerdict(passed=len(p0) == 0, findings=findings)
