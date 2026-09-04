"""VerdictAuthority — único autorizado a PASS/FAIL. LLM no declara PASS.
U10: bridge ForensicCodeContract + ForensicProgrammingEnforcer.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from .forensic_contract import ForensicCodeContract, ForensicContractValidator
from .forensic_core import ForensicProgrammingEnforcer, ForensicEnforcementState
from .evidence import EvidencePacket


class VerdictAuthority:
    def __init__(self, contract: Optional[ForensicCodeContract] = None):
        self.validator = ForensicContractValidator(contract)
        self.enforcer = ForensicProgrammingEnforcer()

    def require_context(self, context_verified: bool, handoff_verified: bool):
        return self.enforcer.require_context(context_verified, handoff_verified)

    def decide(
        self,
        *,
        evidence: Optional[EvidencePacket] = None,
        require_evidence: bool = True,
        state: Optional[ForensicEnforcementState] = None,
    ) -> Dict[str, Any]:
        if state is not None:
            out = self.enforcer.evaluate(state)
            out["authority"] = "VerdictAuthority"
            out["llm_may_declare_pass"] = False
            return out
        if require_evidence:
            if evidence is None or not evidence.is_complete():
                return {
                    "verdict": "FAIL",
                    "reason": "NO EVIDENCE → NO PASS",
                    "authority": "VerdictAuthority",
                    "llm_may_declare_pass": False,
                }
            self.validator.contract.evidence_complete = True
        result = self.validator.validate()
        result["authority"] = "VerdictAuthority"
        result["llm_may_declare_pass"] = False
        return result
