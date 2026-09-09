"""Sheriff 5 estados.
SOURCE: SALIDA_4_CONTRATOS §20 · CAPA DE CONTROL 6
GREEN | YELLOW | ORANGE | RED | BLACK
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SheriffState(str, Enum):
    GREEN = "GREEN"      # aprobado
    YELLOW = "YELLOW"    # necesita revisión
    ORANGE = "ORANGE"    # shadow mode
    RED = "RED"          # rechazado
    BLACK = "BLACK"      # bloqueado permanente


@dataclass(frozen=True)
class SheriffDecision:
    state: SheriffState
    allowed: bool
    reason: str
    contracts: tuple[str, ...] = ()
    details: dict[str, Any] | None = None


def decide(
    *,
    threat_level: str = "normal",
    contracts_ok: bool = True,
    enchufe_ok: bool = True,
    evidence_ok: bool = True,
    permanent_block: bool = False,
) -> SheriffDecision:
    if permanent_block:
        return SheriffDecision(SheriffState.BLACK, False, "bloqueado permanente")
    if threat_level == "quarantine" or not contracts_ok or not enchufe_ok:
        return SheriffDecision(SheriffState.RED, False, "quarantine o contrato/enchufe fallido")
    if not evidence_ok:
        return SheriffDecision(SheriffState.ORANGE, False, "shadow: falta evidencia")
    if threat_level == "sheriff_check":
        return SheriffDecision(SheriffState.YELLOW, True, "aprobado con revisión")
    return SheriffDecision(SheriffState.GREEN, True, "aprobado")
