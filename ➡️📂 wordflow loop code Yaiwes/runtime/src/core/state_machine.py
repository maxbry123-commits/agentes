"""
src/core/state_machine.py
CORE_KERNEL_DETERMINISTA — T-001 (archivo 4/4, cierra el nodo)

Responsabilidad: Maquina de estados finita por node_id. Valida
transiciones permitidas, mantiene historial auditable con timestamp y
expone el estado actual. Es lo que kernel.py invoca via
`await self._state_machine.transition(node_id, "RUNNING" | "FAILED" | "DONE")`.

No requiere secretos. No hace I/O de red. Determinista en su logica de
validacion (el unico elemento no deterministico es el timestamp del
historial, que es solo informativo/auditoria, nunca parte de la logica
de decision).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set, Union

# --------------------------------------------------------------------------
# Estados
# --------------------------------------------------------------------------


class NodeState(str, Enum):
    """Estados posibles del ciclo de vida de un nodo del DAG."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


ALLOWED_TRANSITIONS: Dict[NodeState, Set[NodeState]] = {
    NodeState.PENDING: {NodeState.RUNNING, NodeState.CANCELLED},
    NodeState.RUNNING: {
        NodeState.DONE,
        NodeState.FAILED,
        NodeState.BLOCKED,
        NodeState.CANCELLED,
    },
    NodeState.FAILED: {NodeState.RUNNING, NodeState.CANCELLED},
    NodeState.BLOCKED: {NodeState.RUNNING, NodeState.CANCELLED},
    NodeState.DONE: set(),
    NodeState.CANCELLED: set(),
}

TERMINAL_STATES: Set[NodeState] = {NodeState.DONE, NodeState.CANCELLED}


# --------------------------------------------------------------------------
# Excepciones
# --------------------------------------------------------------------------


class StateMachineError(Exception):
    """Error generico de la maquina de estados."""


class UnknownStateError(StateMachineError):
    """Se recibio un string que no corresponde a ningun NodeState."""


class InvalidTransitionError(StateMachineError):
    """La transicion solicitada no esta permitida desde el estado actual."""

    def __init__(
        self, node_id: str, from_state: NodeState, to_state: NodeState
    ) -> None:
        """Guarda el detalle de la transicion invalida para diagnostico."""
        self.node_id = node_id
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"nodo '{node_id}': transicion invalida "
            f"{from_state.value} -> {to_state.value}"
        )


# --------------------------------------------------------------------------
# Registro de transicion (auditoria)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TransitionRecord:
    """Entrada inmutable del historial de transiciones de un nodo."""

    node_id: str
    from_state: NodeState
    to_state: NodeState
    timestamp: float


# --------------------------------------------------------------------------
# StateMachine
# --------------------------------------------------------------------------


class StateMachine:
    """Maquina de estados finita, thread/async-safe, por node_id."""

    def __init__(self) -> None:
        """Inicializa el mapa de estados actuales y el historial vacio."""
        self._states: Dict[str, NodeState] = {}
        self._history: Dict[str, List[TransitionRecord]] = {}
        self._lock = asyncio.Lock()

    def get_state(self, node_id: str) -> NodeState:
        """Retorna el estado actual de `node_id` (PENDING si no existe)."""
        return self._states.get(node_id, NodeState.PENDING)

    def is_terminal(self, node_id: str) -> bool:
        """True si el nodo esta en un estado terminal (DONE/CANCELLED)."""
        return self.get_state(node_id) in TERMINAL_STATES

    def history(self, node_id: str) -> List[TransitionRecord]:
        """Copia inmutable del historial de transiciones de `node_id`."""
        return list(self._history.get(node_id, []))

    @staticmethod
    def _coerce_state(value: Union[str, NodeState]) -> NodeState:
        """Convierte str -> NodeState. Lanza UnknownStateError si invalido."""
        if isinstance(value, NodeState):
            return value
        try:
            return NodeState(value)
        except ValueError as exc:
            raise UnknownStateError(f"estado desconocido: {value!r}") from exc

    async def transition(
        self, node_id: str, new_state: Union[str, NodeState]
    ) -> NodeState:
        """Aplica una transicion validada y la registra en el historial."""
        target = self._coerce_state(new_state)
        async with self._lock:
            current = self.get_state(node_id)
            if target not in ALLOWED_TRANSITIONS[current]:
                raise InvalidTransitionError(node_id, current, target)
            self._states[node_id] = target
            self._history.setdefault(node_id, []).append(
                TransitionRecord(node_id, current, target, time.time())
            )
            return target

    async def reset(self, node_id: str) -> None:
        """Reinicia `node_id` a PENDING y limpia su historial (uso: retry)."""
        async with self._lock:
            self._states[node_id] = NodeState.PENDING
            self._history[node_id] = []
