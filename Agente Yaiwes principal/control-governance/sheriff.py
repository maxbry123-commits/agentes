"""StandardSheriff — facade over RuleEngine (backward compatible)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from .schema import StandardContract
from .rule_engine import RuleEngine, EngineVerdict, Finding, Severity
from .evidence import EvidencePacket

@dataclass
class SheriffVerdict:
    passed: bool
    findings: List[Finding] = field(default_factory=list)

    @property
    def p0(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == Severity.P0]

class StandardSheriff:
    def __init__(self, contract: Optional[StandardContract] = None):
        self.engine = RuleEngine(contract=contract)

    def evaluate(
        self,
        *,
        file_locs: Optional[Dict[str, int]] = None,
        scan_paths: Optional[List[Path]] = None,
        evidence: Optional[EvidencePacket] = None,
        claim_mvp: bool = False,
        gaps_blocking: int = 0,
        used_ai_as_proof: bool = False,
    ) -> SheriffVerdict:
        v: EngineVerdict = self.engine.evaluate(
            file_locs=file_locs or {},
            scan_paths=scan_paths or [],
            evidence=evidence,
            claim_mvp=claim_mvp,
            gaps_blocking=gaps_blocking,
            used_ai_as_proof=used_ai_as_proof,
        )
        return SheriffVerdict(passed=v.passed, findings=v.findings)
