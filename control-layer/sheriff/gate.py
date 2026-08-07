"""Gate único: SentinelaDecision → Sheriff Verdict (+ shadow append si ORANGE)."""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .estados import SheriffState, Verdict, evaluate_from_sentinela
from .shadow import ShadowLedger, ShadowRecord


def run_sheriff(
    sentinela_decision: Mapping[str, Any],
    *,
    ledger: Optional[ShadowLedger] = None,
    shadow_candidate: bool = False,
    critical_contract_violated: bool = False,
    evidence_missing: bool = False,
) -> tuple[Verdict, ShadowRecord | None]:
    """Evalúa y, si ORANGE, registra en shadow ledger."""
    verdict = evaluate_from_sentinela(
        sentinela_decision,
        shadow_candidate=shadow_candidate,
        critical_contract_violated=critical_contract_violated,
        evidence_missing=evidence_missing,
    )
    shadow_rec: ShadowRecord | None = None
    if verdict.state == SheriffState.ORANGE and ledger is not None:
        shadow_rec = ledger.append(
            op_type=str(sentinela_decision.get("suggested_op_type") or sentinela_decision.get("op_type") or ""),
            set_hash=str(sentinela_decision.get("set_hash") or ""),
            fingerprint_hash=str(sentinela_decision.get("fingerprint_hash") or ""),
            contracts=list(sentinela_decision.get("active_contracts") or []),
            meta={"reasons": list(verdict.reasons)},
        )
    return verdict, shadow_rec
