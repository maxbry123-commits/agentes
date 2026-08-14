# -*- coding: utf-8 -*-
"""StateAuthority — T46. System states machine. 0% LLM."""
from __future__ import annotations

from enum import Enum
from typing import Any


class SystemState(str, Enum):
    CONSTRUIR = "CONSTRUIR"
    VALIDAR = "VALIDAR"
    AUDITAR = "AUDITAR"
    ESPERAR_APROBACION = "ESPERAR_APROBACION"
    REPAIR = "REPAIR"
    DETENIDO = "DETENIDO"
    DEGRADED = "DEGRADED"


ALLOWED: dict[SystemState, set[SystemState]] = {
    SystemState.CONSTRUIR: {
        SystemState.VALIDAR,
        SystemState.DETENIDO,
        SystemState.REPAIR,
    },
    SystemState.VALIDAR: {
        SystemState.AUDITAR,
        SystemState.REPAIR,
        SystemState.CONSTRUIR,
        SystemState.DETENIDO,
    },
    SystemState.AUDITAR: {
        SystemState.ESPERAR_APROBACION,
        SystemState.REPAIR,
        SystemState.DETENIDO,
        SystemState.CONSTRUIR,
    },
    SystemState.ESPERAR_APROBACION: {
        SystemState.CONSTRUIR,
        SystemState.DETENIDO,
        SystemState.REPAIR,
    },
    SystemState.REPAIR: {
        SystemState.CONSTRUIR,
        SystemState.VALIDAR,
        SystemState.DETENIDO,
        SystemState.DEGRADED,
    },
    SystemState.DEGRADED: {
        SystemState.REPAIR,
        SystemState.DETENIDO,
    },
    SystemState.DETENIDO: {
        SystemState.CONSTRUIR,
        SystemState.DETENIDO,
    },
}


class StateAuthority:
    def __init__(self, initial: SystemState = SystemState.CONSTRUIR):
        self.state = initial
        self.history: list[str] = [initial.value]

    def can(self, dst: SystemState) -> bool:
        return dst in ALLOWED.get(self.state, set())

    def transition(self, dst: SystemState, *,
                   reason: str = "") -> dict[str, Any]:
        if not self.can(dst):
            return {
                "ok": False,
                "reason": "INVALID_TRANSITION",
                "from": self.state.value,
                "to": dst.value,
            }
        prev = self.state
        self.state = dst
        self.history.append(dst.value)
        return {
            "ok": True,
            "from": prev.value,
            "to": dst.value,
            "reason": reason or "ok",
            "state": self.state.value,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "history": list(self.history),
            "allowed_next": [s.value for s in ALLOWED.get(self.state, set())],
        }
