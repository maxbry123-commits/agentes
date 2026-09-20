"""9-phase core + Sheriff required · 0% LLM
SOURCE: B2 Loop Engine · loop contracts
Orden estricto. Fases required fallidas = freno.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

PHASE_ORDER = [
    "leer_anclas",
    "plan",
    "ejecutar",
    "medir",
    "validar",
    "reparar",
    "evidencia",
    "checkpoint",
    "decidir",
]

REQUIRED = frozenset({"leer_anclas", "ejecutar", "validar", "evidencia", "decidir"})


@dataclass
class PhaseSpec:
    id: str
    required: bool = False
    skipped: bool = False
    ia_allowed: bool = False


@dataclass
class PhaseResult:
    phase: str
    ok: bool
    skipped: bool = False
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class SheriffVerdict:
    ok: bool
    missing_required: list[str] = field(default_factory=list)
    failed_required: list[str] = field(default_factory=list)
    reason: str = ""


def default_phase_specs() -> list[PhaseSpec]:
    return [
        PhaseSpec(id=p, required=(p in REQUIRED), ia_allowed=(p in ("plan", "ejecutar", "reparar")))
        for p in PHASE_ORDER
    ]


class Sheriff:
    """Frena si falta o falla fase obligatoria."""

    def check(self, results: list[PhaseResult], specs: list[PhaseSpec] | None = None) -> SheriffVerdict:
        specs = specs or default_phase_specs()
        req = {s.id for s in specs if s.required}
        by_id = {r.phase: r for r in results}
        missing = [p for p in req if p not in by_id and not any(s.id == p and s.skipped for s in specs)]
        # skipped required is still missing
        for s in specs:
            if s.required and s.skipped:
                if s.id not in missing:
                    missing.append(s.id)
        failed = [r.phase for r in results if r.phase in req and not r.ok and not r.skipped]
        ok = len(missing) == 0 and len(failed) == 0
        reason = ""
        if missing:
            reason = f"missing required: {missing}"
        elif failed:
            reason = f"failed required: {failed}"
        return SheriffVerdict(ok=ok, missing_required=missing, failed_required=failed, reason=reason)


PhaseHandler = Callable[[dict[str, Any]], PhaseResult]


class PhaseRunner:
    """Ejecuta fases en orden. Handlers opcionales (default no-op ok)."""

    def __init__(self, handlers: dict[str, PhaseHandler] | None = None, specs: list[PhaseSpec] | None = None):
        self.handlers = handlers or {}
        self.specs = specs or default_phase_specs()
        self.sheriff = Sheriff()

    def run(self, context: dict[str, Any] | None = None, *, stop_on_required_fail: bool = True) -> tuple[list[PhaseResult], SheriffVerdict]:
        ctx = dict(context or {})
        results: list[PhaseResult] = []
        for spec in self.specs:
            if spec.skipped:
                results.append(PhaseResult(phase=spec.id, ok=True, skipped=True))
                continue
            handler = self.handlers.get(spec.id)
            if handler is None:
                # default: pass-through ok (skeleton)
                res = PhaseResult(phase=spec.id, ok=True, output={})
            else:
                try:
                    res = handler(ctx)
                    res.phase = spec.id
                except Exception as e:  # noqa: BLE001 — boundary
                    res = PhaseResult(phase=spec.id, ok=False, error=str(e))
            results.append(res)
            if res.ok and res.output:
                ctx.update(res.output)
            if stop_on_required_fail and spec.required and not res.ok:
                break
        verdict = self.sheriff.check(results, self.specs)
        return results, verdict
