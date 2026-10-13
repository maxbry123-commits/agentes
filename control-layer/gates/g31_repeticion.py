"""G31 Repetición — si ya se resolvió, devolver resultado guardado.
SOURCE: SALIDA_6 · IA 0%
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class G31Result:
    hit: bool
    cached: dict[str, Any] | None


def g31_repeticion(task_key: str, store: dict[str, dict[str, Any]]) -> G31Result:
    if task_key in store:
        return G31Result(True, store[task_key])
    return G31Result(False, None)
