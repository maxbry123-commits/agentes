# -*- coding: utf-8 -*-
"""GuardedParallelRuntime — T23/G6. Retry + CircuitBreaker over ParallelRuntime.

SCOPE (G6 / gap G-S4-03):
  - IN SCOPE: parallel task handlers (sandbox/lease slots).
  - OUT OF SCOPE: RuntimeBus engine jobs, ExecutionFacade, Manifest signing.
  - Bus-level retry must be added beside Bus.dispatch if needed — not here.
  - Use ParallelFacadeRuntime (G5) when tasks need engine/resource routing.

0% LLM.
"""
from __future__ import annotations

from typing import Any, Callable

from .circuit_breaker import CircuitBreaker, CircuitOpenError
from .parallel_runtime import ParallelRuntime
from .retry_policy import RetryExhaustedError, RetryPolicy

SCOPE = {
    "in": ["parallel_tasks", "sandbox_slots", "leases", "retry", "circuit_breaker"],
    "out": ["runtime_bus", "execution_manifest", "execution_facade", "engine_abi"],
}


class GuardedParallelRuntime(ParallelRuntime):
    """Wraps handler with retry + optional circuit breaker per runtime."""

    def __init__(
        self,
        *,
        n_workers: int = 2,
        n_sandboxes: int | None = None,
        lease_ttl_s: float = 60.0,
        lease_clock: Any = None,
        retry: RetryPolicy | None = None,
        circuit: CircuitBreaker | None = None,
    ):
        super().__init__(
            n_workers=n_workers,
            n_sandboxes=n_sandboxes,
            lease_ttl_s=lease_ttl_s,
            lease_clock=lease_clock,
        )
        self.retry = retry or RetryPolicy(max_attempts=1)
        self.circuit = circuit

    def scope(self) -> dict[str, list[str]]:
        return dict(SCOPE)

    def run(
        self,
        handler: Callable[[dict[str, Any]], bool],
        *,
        max_steps: int = 1000,
    ) -> dict[str, Any]:
        def guarded(ctx: dict[str, Any]) -> bool:
            def once() -> bool:
                if self.circuit is not None and not self.circuit.allow():
                    raise CircuitOpenError(
                        self.circuit.name,
                        (self.circuit.opened_at or 0) + self.circuit.recovery_timeout_s,
                    )
                try:
                    ok = bool(handler(ctx))
                except Exception:
                    if self.circuit is not None:
                        self.circuit.record_failure()
                    raise
                if self.circuit is not None:
                    if ok:
                        self.circuit.record_success()
                    else:
                        self.circuit.record_failure()
                if not ok:
                    raise RuntimeError("handler_returned_false")
                return True

            try:
                self.retry.run(once, sleeper=lambda _d: None)
                return True
            except (RetryExhaustedError, CircuitOpenError):
                return False

        result = super().run(guarded, max_steps=max_steps)
        result["circuit"] = self.circuit.snapshot() if self.circuit else None
        result["retry_plan"] = self.retry.plan()
        result["scope"] = self.scope()
        return result
