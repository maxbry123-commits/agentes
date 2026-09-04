"""Persistencia determinista Wordflow LOOP Yaiwes.

Patrón fuente: OpenMythos Prelude -> Recurrent Block -> Coda.
Adaptación NO neuronal: el INPUT/contrato original se reinserta en cada ciclo.
Cuando una verificación falla, exige exactamente 20 alternativas de recuperación
antes de reintentar. No hay llamadas LLM en esta capa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Callable, Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PersistenceContract:
    recurrent_depth: int = 20
    recovery_alternatives: int = 20
    require_evidence: bool = True


@dataclass
class CycleEvidence(Generic[T]):
    cycle: int
    state: T
    state_hash: str
    passed: bool
    recovery_count: int = 0


@dataclass
class PersistenceTrace(Generic[T]):
    prelude: T
    cycles: list[CycleEvidence[T]] = field(default_factory=list)
    coda: T | None = None
    closed: bool = False


def _digest(value: object) -> str:
    return sha256(repr(value).encode("utf-8")).hexdigest()


def run_persistence_loop(
    input_state: T,
    prelude: Callable[[T], T],
    recurrent_step: Callable[[T, T, int], T],
    verify_refute: Callable[[T], bool],
    research_20: Callable[[T, T], Sequence[T]],
    apply_recovery: Callable[[T, Sequence[T]], T],
    coda: Callable[[T], T],
    contract: PersistenceContract = PersistenceContract(),
) -> PersistenceTrace[T]:
    """Ejecuta Prelude una vez, persistencia recurrente y Coda al cerrar.

    Cada ciclo reinyecta ``anchor`` para impedir deriva del objetivo. Si falla
    verify/refute, ``research_20`` debe producir exactamente 20 alternativas;
    la selección/aplicación la hace ``apply_recovery`` de forma determinista.
    El bloque continúa hasta PASS; recurrent_depth=20 define la profundidad
    repetitiva por ronda, no una afirmación de rendimiento 20x.
    """
    if contract.recurrent_depth != 20 or contract.recovery_alternatives != 20:
        raise ValueError("Contrato exige profundidad 20 y 20 alternativas de recuperación")

    anchor = prelude(input_state)
    trace = PersistenceTrace(prelude=anchor)
    current = anchor
    cycle = 0

    while True:
        cycle += 1
        iteration = ((cycle - 1) % contract.recurrent_depth) + 1
        current = recurrent_step(current, anchor, iteration)
        passed = bool(verify_refute(current))
        recovery_count = 0

        if not passed:
            alternatives = tuple(research_20(current, anchor))
            recovery_count = len(alternatives)
            if recovery_count != contract.recovery_alternatives:
                raise RuntimeError(
                    f"research_20 debe devolver 20 alternativas; devolvió {recovery_count}"
                )
            current = apply_recovery(current, alternatives)
            passed = bool(verify_refute(current))

        trace.cycles.append(
            CycleEvidence(cycle, current, _digest(current), passed, recovery_count)
        )
        if passed:
            trace.coda = coda(current)
            trace.closed = True
            break

    if contract.require_evidence and not trace.cycles:
        raise RuntimeError("Persistencia sin evidencia")
    return trace


PLUGIN_CONTRACT = {
    "plugin_id": "wordflow.persistence.open_mythos_loop",
    "version": "2.0.0",
    "entrypoint": "run_persistence_loop",
    "deterministic": True,
    "llm_allowed": False,
    "recurrent_depth": 20,
    "recovery_alternatives": 20,
    "pattern": "prelude_recurrent_coda_with_input_reinjection",
}
