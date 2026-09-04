# -*- coding: utf-8 -*-
"""control/reverse.py — Reverse Dependency Check 0% LLM.
Fuente: SALIDA 4 §14.6
Detecta conflictos: A requiere X, B prohíbe X.
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple


# prohibiciones seed: contrato → set de ids incompatibles
DEFAULT_FORBID: Dict[str, List[str]] = {
    "C47": ["C99_UNSAFE"],  # placeholder seed
    "C48": [],
    "C85": [],
}


def reverse_check(
    ordered: List[str],
    forbid: Dict[str, List[str]] | None = None,
) -> Tuple[bool, List[str]]:
    """
    True, [] si sin conflictos.
    False, [msgs] si hay prohibiciones cruzadas.
    """
    fb = forbid or DEFAULT_FORBID
    present: Set[str] = set(ordered)
    conflicts: List[str] = []
    for c in ordered:
        for bad in fb.get(c, []):
            if bad in present:
                conflicts.append(f"{c} forbids {bad}")
    return (len(conflicts) == 0, conflicts)
