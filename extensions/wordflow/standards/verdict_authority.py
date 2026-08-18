"""VerdictAuthority — único componente autorizado a PASS/FAIL/CLOSED (Salida 2)."""
from __future__ import annotations
from typing import Dict, Any, Optional
from .forensic_contract import ForensicCodeContract, ForensicContractValidator
from .evidence import EvidencePacket

class VerdictAuthority:
    """Ni GPT ni Claude ni Grok declaran PASS. Solo este motor."""

    def __init__(self, contract: Optional[ForensicCodeContract] = None):
        self.validator = ForensicContractValidator(contract)

    def decide(
        self,
        *,
        evidence: Optional[EvidencePacket] = None,
        require_evidence: bool = True,
    ) -> Dict[str, Any]:
        if require_evidence:
            if evidence is None or not evidence.is_complete():
                return {
                    "verdict": "FAIL",
                    "reason": "NO EVIDENCE → NO PASS",
                    "authority": "VerdictAuthority",
                }
            self.validator.contract.evidence_complete = True
        result = self.validator.validate()
        result["authority"] = "VerdictAuthority"
        result["llm_may_declare_pass"] = False
        return result
