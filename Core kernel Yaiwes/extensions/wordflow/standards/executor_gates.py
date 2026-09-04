"""Gates ejecutor: pre COPY-FIRST + checklist sheriff + post forensic."""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from pathlib import Path
from .copy_first import ExistingCodeScanner, CopyFirstResult
from .forensic_contract import ForensicCodeContract, ForensicContractValidator
from .verdict_authority import VerdictAuthority
from .evidence import EvidencePacket
from .forensic_report import render_forensic_report
from .checklist_sheriff import ChecklistSheriff, AgentChecklistClaim, SheriffVerdict

class ExecutorPreImplementGate:
    def __init__(self, scan_roots: Optional[List[Path]] = None):
        self.scanner = ExistingCodeScanner(scan_roots or [])
        self.validator = ForensicContractValidator()
        self.sheriff = ChecklistSheriff()

    def check(
        self,
        *,
        context_verified: bool,
        handoff_verified: bool,
        symbol_or_stem: str,
        dest: str,
        checklist: Optional[AgentChecklistClaim] = None,
        require_checklist: bool = True,
    ) -> Dict[str, Any]:
        self.validator.contract.context_verified = context_verified
        self.validator.contract.handoff_verified = handoff_verified
        block = self.validator.block_if_no_context()
        if block:
            return {"allow": False, "reason": block, "copy_first": None, "checklist": None}

        cf: CopyFirstResult = self.scanner.plan(symbol_or_stem=symbol_or_stem, dest=dest)

        checklist_result = None
        if require_checklist:
            if checklist is None:
                return {
                    "allow": False,
                    "reason": "BLOCK: checklist obligatoria ausente (agente debe enviar AgentChecklistClaim)",
                    "copy_first": {
                        "action": cf.plan.action,
                        "blocked_generate": cf.blocked_generate,
                        "sources": [s.path for s in cf.plan.sources],
                    },
                    "checklist": None,
                }
            # alinear action con scanner
            if cf.blocked_generate and checklist.action == "GENERATE":
                checklist.action = "ADAPT"
                checklist.sources = [s.path for s in cf.plan.sources]
            sv: SheriffVerdict = self.sheriff.evaluate(checklist)
            checklist_result = sv.to_dict()
            if not sv.passed:
                return {
                    "allow": False,
                    "reason": "BLOCK: ChecklistSheriff FAIL",
                    "copy_first": {
                        "action": cf.plan.action,
                        "blocked_generate": cf.blocked_generate,
                        "sources": [s.path for s in cf.plan.sources],
                    },
                    "checklist": checklist_result,
                }

        return {
            "allow": True,
            "reason": "pre-implement OK",
            "copy_first": {
                "action": cf.plan.action,
                "blocked_generate": cf.blocked_generate,
                "message": cf.message,
                "sources": [s.path for s in cf.plan.sources],
            },
            "checklist": checklist_result,
            "policy": "COPY/MOVE → LINK → PATCH → ADAPT → GENERATE LAST; checklist required",
        }

class ExecutorPostVerifyGate:
    def __init__(self):
        self.authority = VerdictAuthority()
        self.sheriff = ChecklistSheriff()

    def verify(
        self,
        contract: ForensicCodeContract,
        evidence: Optional[EvidencePacket] = None,
        checklist: Optional[AgentChecklistClaim] = None,
        require_checklist: bool = True,
    ) -> Dict[str, Any]:
        if require_checklist:
            if checklist is None:
                return {
                    "verdict": "FAIL",
                    "reason": "BLOCK: checklist ausente en post_verify",
                    "authority": "ChecklistSheriff+VerdictAuthority",
                }
            sv = self.sheriff.evaluate(checklist)
            if not sv.passed:
                return {
                    "verdict": "FAIL",
                    "reason": "BLOCK: ChecklistSheriff FAIL en post",
                    "checklist": sv.to_dict(),
                    "authority": "ChecklistSheriff",
                }
        self.authority.validator.contract = contract
        decision = self.authority.decide(evidence=evidence, require_evidence=True)
        report = render_forensic_report(contract, decision.get("verdict", "FAIL"))
        decision["forensic_report"] = report
        if checklist is not None:
            decision["checklist"] = self.sheriff.evaluate(checklist).to_dict()
        return decision
