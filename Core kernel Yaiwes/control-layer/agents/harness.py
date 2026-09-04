"""W08 · Universal Harness · prepare/load/execute/inspect/cancel/cleanup."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Optional


@dataclass
class HarnessResult:
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class UniversalHarness:
    """Interfaz única hacia cualquier agente/adapter."""

    def __init__(self, agent_id: str, executor: Callable[..., dict[str, Any]] | None = None) -> None:
        self.agent_id = agent_id
        self._executor = executor
        self._ctx: dict[str, Any] = {}
        self._cancelled = False

    def prepare(self, context: dict[str, Any] | None = None) -> None:
        self._ctx = dict(context or {})
        self._cancelled = False

    def load_context(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        if extra:
            self._ctx.update(extra)
        return dict(self._ctx)

    def execute(self, payload: dict[str, Any] | None = None) -> HarnessResult:
        if self._cancelled:
            return HarnessResult(ok=False, error="cancelled")
        if self._executor is None:
            return HarnessResult(
                ok=True,
                output={"echo": payload or {}, "agent_id": self.agent_id},
                evidence={"mode": "stub"},
            )
        try:
            out = self._executor(dict(payload or {}), dict(self._ctx))
            return HarnessResult(ok=True, output=dict(out or {}), evidence={"agent_id": self.agent_id})
        except Exception as e:  # noqa: BLE001
            return HarnessResult(ok=False, error=str(e))

    def inspect(self) -> dict[str, Any]:
        return {"agent_id": self.agent_id, "cancelled": self._cancelled, "ctx_keys": list(self._ctx)}

    def cancel(self) -> None:
        self._cancelled = True

    def cleanup(self) -> None:
        self._ctx.clear()
        self._cancelled = False
