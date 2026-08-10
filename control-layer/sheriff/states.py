# -*- coding: utf-8 -*-
"""sheriff/states.py — Sheriff 5 estados. 0% LLM.
Fuente: SALIDA 4 §20 · SALIDA 6 §17
GREEN YELLOW ORANGE RED BLACK
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class SheriffState(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    BLACK = "BLACK"


# transiciones permitidas (deterministas)
ALLOWED: Dict[SheriffState, Set[SheriffState]] = {
    SheriffState.GREEN: {SheriffState.GREEN, SheriffState.YELLOW, SheriffState.ORANGE},
    SheriffState.YELLOW: {SheriffState.GREEN, SheriffState.YELLOW, SheriffState.ORANGE, SheriffState.RED},
    SheriffState.ORANGE: {SheriffState.YELLOW, SheriffState.ORANGE, SheriffState.RED},
    SheriffState.RED: {SheriffState.ORANGE, SheriffState.RED, SheriffState.BLACK},
    SheriffState.BLACK: {SheriffState.BLACK},  # terminal hasta recovery externa
}


def can_transition(src: SheriffState, dst: SheriffState) -> bool:
    return dst in ALLOWED.get(src, set())


def state_from_band(band: str, risk_score: int) -> SheriffState:
    """Mapea threat.band + score → estado inicial."""
    b = (band or "").lower()
    if b == "quarantine" or risk_score >= 8:
        return SheriffState.RED
    if b == "sheriff_check" or risk_score >= 4:
        return SheriffState.YELLOW
    return SheriffState.GREEN
