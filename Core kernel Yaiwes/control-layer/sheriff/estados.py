"""Sheriff 5 estados · GREEN / YELLOW / ORANGE / RED / BLACK · 0% LLM.

Fuente: S9-DOC2. ORANGE = shadow mode (C55 promotion path).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class SheriffState(str, Enum):
    GREEN = "GREEN"       # ejecuta
    YELLOW = "YELLOW"     # ejecuta + audit extra
    ORANGE = "ORANGE"     # shadow: registra, no promueve a prod path
    RED = "RED"           # bloquea hasta remediar
    BLACK = "BLACK"       # bloqueo duro + quarantine


@dataclass(frozen=True)
class Verdict:
    state: SheriffState
    reasons: tuple[str, ...]
    allow_execute: bool
    require_audit: bool
    shadow_only: bool
    active_contracts: tuple[str, ...]
    process_plan: tuple[str, ...]
    risk_score: int
    band: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        return d


def evaluate(
    *,
    risk_score: int,
    band: str,
    elevated: bool,
    block_execution: bool,
    active_contracts: Sequence[str],
    process_plan: Sequence[str],
    sheriff_required: bool = False,
    shadow_candidate: bool = False,
    critical_contract_violated: bool = False,
    evidence_missing: bool = False,
) -> Verdict:
    """Decide estado Sheriff de forma determinista.

    Prioridad (alta → baja):
    BLACK > RED > ORANGE > YELLOW > GREEN
    """
    reasons: list[str] = []
    contracts = tuple(active_contracts)
    plan = tuple(process_plan)

    # BLACK: violación crítica o evidence obligatoria ausente en path de riesgo
    if critical_contract_violated:
        reasons.append("critical_contract_violated")
        return Verdict(
            state=SheriffState.BLACK,
            reasons=tuple(reasons),
            allow_execute=False,
            require_audit=True,
            shadow_only=False,
            active_contracts=contracts,
            process_plan=plan,
            risk_score=risk_score,
            band=band,
        )

    if evidence_missing and (elevated or band == "quarantine" or "C49" in contracts):
        reasons.append("evidence_missing_on_risk_path")
        return Verdict(
            state=SheriffState.BLACK,
            reasons=tuple(reasons),
            allow_execute=False,
            require_audit=True,
            shadow_only=False,
            active_contracts=contracts,
            process_plan=plan,
            risk_score=risk_score,
            band=band,
        )

    # RED: block_execution o quarantine con credential
    if block_execution or (band == "quarantine" and elevated):
        reasons.append("block_execution" if block_execution else "quarantine_elevated")
        return Verdict(
            state=SheriffState.RED,
            reasons=tuple(reasons),
            allow_execute=False,
            require_audit=True,
            shadow_only=False,
            active_contracts=contracts,
            process_plan=plan,
            risk_score=risk_score,
            band=band,
        )

    # ORANGE: shadow / C55 promotion candidate
    if shadow_candidate or "C55" in contracts:
        reasons.append("shadow_or_C55")
        return Verdict(
            state=SheriffState.ORANGE,
            reasons=tuple(reasons),
            allow_execute=True,   # ejecuta en shadow, no escribe prod irreversible
            require_audit=True,
            shadow_only=True,
            active_contracts=contracts,
            process_plan=plan,
            risk_score=risk_score,
            band=band,
        )

    # YELLOW: sheriff_check band o risk medio
    if sheriff_required or band == "sheriff_check" or risk_score >= 4:
        reasons.append("sheriff_check_or_risk_mid")
        return Verdict(
            state=SheriffState.YELLOW,
            reasons=tuple(reasons),
            allow_execute=True,
            require_audit=True,
            shadow_only=False,
            active_contracts=contracts,
            process_plan=plan,
            risk_score=risk_score,
            band=band,
        )

    # GREEN
    reasons.append("normal_path")
    return Verdict(
        state=SheriffState.GREEN,
        reasons=tuple(reasons),
        allow_execute=True,
        require_audit=False,
        shadow_only=False,
        active_contracts=contracts,
        process_plan=plan,
        risk_score=risk_score,
        band=band,
    )


def evaluate_from_sentinela(decision: Mapping[str, Any], **kwargs: Any) -> Verdict:
    """Adapter desde SentinelaDecision.to_dict()."""
    return evaluate(
        risk_score=int(decision.get("risk_score", 0)),
        band=str(decision.get("band", "normal")),
        elevated=bool(decision.get("elevated", False)),
        block_execution=bool(decision.get("block_execution", False)),
        active_contracts=tuple(decision.get("active_contracts") or ()),
        process_plan=tuple(decision.get("process_plan") or ()),
        sheriff_required=bool(decision.get("sheriff_required", False)),
        **kwargs,
    )
