"""MHYTOS strategy executor — 6 fases paralelas conceptuales · 0% LLM core
SOURCE: P3 · strategy=adversarial|consensus|parallel
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable

MHYTOS_PHASES = [
    "investigation",
    "planning",
    "execution",
    "improvements",
    "review",
    "strategy",
]


@dataclass
class PhaseOut:
    phase: str
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


PhaseFn = Callable[[str, dict[str, Any]], PhaseOut]


class MHYTOSExecutor:
    """Ejecuta 6 fases; parallel=True usa threads (determinista en merge)."""

    def __init__(self, handlers: dict[str, PhaseFn] | None = None, max_workers: int = 6) -> None:
        self.handlers = handlers or {}
        self.max_workers = max_workers

    def run(self, context: dict[str, Any] | None = None, *, parallel: bool = True) -> list[PhaseOut]:
        ctx = dict(context or {})
        results: list[PhaseOut] = []

        def _one(phase: str) -> PhaseOut:
            fn = self.handlers.get(phase)
            if fn is None:
                return PhaseOut(phase=phase, ok=True, output={})
            try:
                return fn(phase, ctx)
            except Exception as e:  # noqa: BLE001
                return PhaseOut(phase=phase, ok=False, error=str(e))

        if not parallel:
            for p in MHYTOS_PHASES:
                r = _one(p)
                results.append(r)
                if r.ok and r.output:
                    ctx.update(r.output)
            return results

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futs = {pool.submit(_one, p): p for p in MHYTOS_PHASES}
            by_phase: dict[str, PhaseOut] = {}
            for fut in as_completed(futs):
                r = fut.result()
                by_phase[r.phase] = r
        # merge determinista por orden canónico
        for p in MHYTOS_PHASES:
            results.append(by_phase[p])
            if by_phase[p].ok and by_phase[p].output:
                ctx.update(by_phase[p].output)
        return results

    def all_ok(self, results: list[PhaseOut]) -> bool:
        return all(r.ok for r in results)
