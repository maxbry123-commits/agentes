# -*- coding: utf-8 -*-
"""RecoveryEngine — T33. Deterministic recovery levels. 0% LLM.

Levels (subset N07 deferred strategies):
  RETRY | CHECKPOINT_RESTORE | SANDBOX_RESTART | ENGINE_FALLBACK | ESCALATE
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from .checkpoint_store import CheckpointStore
from .circuit_breaker import CircuitBreaker
from .retry_policy import RetryExhaustedError, RetryPolicy
from .sandbox_manager import SandboxManager


class RecoveryAction(str, Enum):
    RETRY = "RETRY"
    CHECKPOINT_RESTORE = "CHECKPOINT_RESTORE"
    SANDBOX_RESTART = "SANDBOX_RESTART"
    ENGINE_FALLBACK = "ENGINE_FALLBACK"
    ESCALATE = "ESCALATE"


def choose_action(
    *,
    attempts: int,
    max_attempts: int,
    has_checkpoint: bool,
    sandbox_dead: bool,
    circuit_open: bool,
) -> RecoveryAction:
    if circuit_open:
        return RecoveryAction.ESCALATE
    if sandbox_dead:
        return RecoveryAction.SANDBOX_RESTART
    if has_checkpoint and attempts >= max_attempts:
        return RecoveryAction.CHECKPOINT_RESTORE
    if attempts < max_attempts:
        return RecoveryAction.RETRY
    return RecoveryAction.ESCALATE


class RecoveryEngine:
    def __init__(
        self,
        *,
        retry: RetryPolicy | None = None,
        checkpoints: CheckpointStore | None = None,
        sandboxes: SandboxManager | None = None,
        circuit: CircuitBreaker | None = None,
        fallback_engine_id: str = "fake_static",
    ):
        self.retry = retry or RetryPolicy(max_attempts=3)
        self.checkpoints = checkpoints or CheckpointStore()
        self.sandboxes = sandboxes
        self.circuit = circuit
        self.fallback_engine_id = fallback_engine_id
        self.history: list[dict[str, Any]] = []

    def plan(
        self,
        *,
        attempts: int = 0,
        checkpoint_id: str | None = None,
        sandbox_id: str | None = None,
        sandbox_dead: bool = False,
    ) -> dict[str, Any]:
        circuit_open = False
        if self.circuit is not None:
            circuit_open = not self.circuit.allow()
        has_cp = bool(checkpoint_id) and (
            checkpoint_id in getattr(self.checkpoints, "_items", {})
            or self.checkpoints.get(checkpoint_id) is not None
            if hasattr(self.checkpoints, "get")
            else bool(checkpoint_id)
        )
        # robust has_checkpoint
        if checkpoint_id and hasattr(self.checkpoints, "get"):
            try:
                has_cp = self.checkpoints.get(checkpoint_id) is not None
            except Exception:
                has_cp = False
        elif checkpoint_id:
            has_cp = True

        action = choose_action(
            attempts=attempts,
            max_attempts=self.retry.max_attempts,
            has_checkpoint=has_cp,
            sandbox_dead=sandbox_dead,
            circuit_open=circuit_open,
        )
        plan = {
            "action": action.value,
            "attempts": attempts,
            "checkpoint_id": checkpoint_id,
            "sandbox_id": sandbox_id,
            "fallback_engine_id": self.fallback_engine_id
            if action == RecoveryAction.ENGINE_FALLBACK
            else None,
        }
        self.history.append(plan)
        return plan

    def run_with_retry(self, fn: Callable[[], Any]) -> dict[str, Any]:
        try:
            val = self.retry.run(fn, sleeper=lambda _d: None)
            return {"ok": True, "result": val, "action": RecoveryAction.RETRY.value}
        except RetryExhaustedError as exc:
            return {
                "ok": False,
                "action": RecoveryAction.ESCALATE.value,
                "error": str(exc),
            }
