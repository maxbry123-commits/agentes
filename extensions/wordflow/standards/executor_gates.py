"""Gates del ejecutor de programación Wordflow — pre-IMPLEMENT + post-verify."""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from pathlib import Path
from .copy_first import ExistingCodeScanner, CopyFirstResult
from .forensic_contract import ForensicCodeContract, ForensicContractValidator
from .verdict_authority import VerdictAuthority
from .evidence import EvidencePacket
from .forensic_report import render_forensic_report

class ExecutorPreImplementGate:
    """Antes de escribir code: context/handoff + COPY-FIRST."""

    def __init__(self, scan_roots: Optional[List[Path]] = None):
        self.scanner = ExistingCodeScanner(scan_roots or [])
        self.validator = ForensicContractValidator()

    def check(
        self,
        *,
        context_verified: bool,
        handoff_verified: bool,
        symbol_or_stem: str,
        dest: str,
    ) -> Dict[str, Any]:
        self.validator.contract.context_verified = context_verified
        self.validator.contract.handoff_verified = handoff_verified
        block = self.validator.block_if_no_context()
        if block:
            return {"allow": False, "reason": block, "copy_first": None}
        cf: CopyFirstResult = self.scanner.plan(symbol_or_stem=symbol_or_stem, dest=dest)
        return {
            "allow": True,
            "reason": "pre-implement OK",
            "copy_first": {
                "action": cf.plan.action,
                "blocked_generate": cf.blocked_generate,
                "message": cf.message,
                "sources": [s.path for s in cf.plan.sources],
            },
            "policy": "COPY/MOVE → LINK → PATCH → ADAPT → GENERATE LAST",
        }

class ExecutorPostVerifyGate:
    """Después de implementar: auditoría forense de programación (mismo contrato)."""

    def __init__(self):
        self.authority = VerdictAuthority()

    def verify(self, contract: ForensicCodeContract, evidence: Optional[EvidencePacket] = None) -> Dict[str, Any]:
        self.authority.validator.contract = contract
        decision = self.authority.decide(evidence=evidence, require_evidence=True)
        report = render_forensic_report(contract, decision.get("verdict", "FAIL"))
        decision["forensic_report"] = report
        return decision
