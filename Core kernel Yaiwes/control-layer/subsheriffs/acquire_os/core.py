"""Acquire Engine core — sequential gated steps from Recipe."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .verify import run_verify_steps
from .build import run_build_steps
from .promote import run_promote_steps


@dataclass
class StepResult:
    name: str
    status: str  # PASS | FAILED | SKIPPED_EXPECTED
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class AcquireContext:
    recipe: dict[str, Any]
    work_root: str
    results: list[StepResult] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)

    def record(self, name: str, status: str, **detail):
        self.results.append(StepResult(name, status, detail))

    def has_failed(self) -> bool:
        return any(r.status == "FAILED" for r in self.results)


def gate(ctx: AcquireContext, name: str, fn: Callable[[AcquireContext], str]):
    if ctx.has_failed():
        ctx.record(name, "SKIPPED_EXPECTED", reason="prior_failed")
        return
    try:
        status = fn(ctx)
        if status not in ("PASS", "FAILED", "SKIPPED_EXPECTED"):
            status = "FAILED"
        ctx.record(name, status)
    except Exception as e:  # noqa: BLE001
        ctx.record(name, "FAILED", error=type(e).__name__, msg=str(e)[:200])


class AcquireEngine:
    def run(self, recipe: dict[str, Any], work_root: str) -> AcquireContext:
        ctx = AcquireContext(recipe=recipe, work_root=work_root)
        # verify phase
        for name, fn in run_verify_steps():
            gate(ctx, name, fn)
        # build phase
        for name, fn in run_build_steps():
            gate(ctx, name, fn)
        # promote only if no FAILED
        for name, fn in run_promote_steps():
            if name.startswith("PROMOTE") and ctx.has_failed():
                ctx.record(name, "SKIPPED_EXPECTED", reason="has_failed")
                continue
            gate(ctx, name, fn)
        return ctx
