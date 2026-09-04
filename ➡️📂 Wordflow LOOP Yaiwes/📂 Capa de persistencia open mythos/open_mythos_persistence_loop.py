"""Capa de persistencia recurrente para Wordflow LOOP Yaiwes.

Mecanismo adoptado de OpenMythos: Prelude -> Recurrent Block -> Coda.
No copia el modelo neuronal: aplica el patrón al estado de workflow.
El bucle es determinista y está limitado a 20 iteraciones.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PersistenceContract:
    max_loops: int = 20
    require_stable_evidence: bool = True


@dataclass
class PersistenceTrace(Generic[T]):
    prelude: T
    states: list[T] = field(default_factory=list)
    evidence_hashes: list[str] = field(default_factory=list)
    coda: T | None = None


def _digest(value: object) -> str:
    return sha256(repr(value).encode("utf-8")).hexdigest()


def run_persistence_loop(
    input_state: T,
    prelude: Callable[[T], T],
    recurrent_step: Callable[[T, T, int], T],
    coda: Callable[[T], T],
    is_complete: Callable[[T], bool],
    contract: PersistenceContract = PersistenceContract(),
) -> PersistenceTrace[T]:
    """Prelude once, recurrent persistence up to 20x, Coda once.

    The original prelude state is reinjected into every recurrent step so the
    task contract cannot silently drift. No LLM call exists in this layer.
    """
    if contract.max_loops != 20:
        raise ValueError("Wordflow persistence contract requires exactly 20 max loops")

    anchor = prelude(input_state)
    trace = PersistenceTrace(prelude=anchor)
    current = anchor

    for iteration in range(1, contract.max_loops + 1):
        current = recurrent_step(current, anchor, iteration)
        trace.states.append(current)
        trace.evidence_hashes.append(_digest(current))
        if is_complete(current):
            break

    trace.coda = coda(current)
    if contract.require_stable_evidence and not trace.evidence_hashes:
        raise RuntimeError("Persistence loop produced no evidence")
    return trace


# Universal Plug hook: the bus/adapter may discover this descriptor without
# coupling this layer to the kernel implementation.
PLUGIN_CONTRACT = {
    "plugin_id": "wordflow.persistence.open_mythos_loop",
    "version": "1.0.0",
    "entrypoint": "run_persistence_loop",
    "deterministic": True,
    "llm_allowed": False,
    "max_loops": 20,
    "pattern": "prelude_recurrent_coda",
}
