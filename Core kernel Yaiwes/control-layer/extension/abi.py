"""ABI extensión kernel · v1.0.0 · sin imports de vendor OpenClaw.

Contrato mínimo que cualquier host (OpenClaw / TEAM / mock) implementa
o invoca:

  load(ctx) → ok
  unload()
  health() → dict
  capabilities() → list[str]
  contracts() → list[str]
  execute(capability, params, nivel) → evidence_output
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Protocol

ABI_VERSION = "1.0.0"


@dataclass
class EvidenceOutput:
    ok: bool
    capability: str
    evidence_hash: str
    set_hash: str | None = None
    sheriff_state: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthReport:
    status: str  # ok | degraded | down
    abi_version: str
    loaded: bool
    uptime_sec: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExtensionABI(Protocol):
    def load(self, ctx: Mapping[str, Any]) -> bool: ...
    def unload(self) -> None: ...
    def health(self) -> HealthReport: ...
    def capabilities(self) -> list[str]: ...
    def contracts(self) -> list[str]: ...
    def execute(
        self,
        capability: str,
        params: Mapping[str, Any] | None = None,
        nivel: str = "MID",
    ) -> EvidenceOutput: ...


class WordflowExtension:
    """Implementación de referencia del ABI (núcleo dual)."""

    def __init__(self) -> None:
        self._loaded = False
        self._ctx: dict[str, Any] = {}
        self._t0 = 0.0
        self._handlers: Dict[str, Callable[..., EvidenceOutput]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._handlers["ping"] = self._cap_ping
        self._handlers["route_op"] = self._cap_route_op
        self._handlers["sheriff_gate"] = self._cap_sheriff_gate

    def load(self, ctx: Mapping[str, Any]) -> bool:
        self._ctx = dict(ctx or {})
        self._loaded = True
        self._t0 = time.time()
        return True

    def unload(self) -> None:
        self._loaded = False
        self._ctx = {}

    def health(self) -> HealthReport:
        if not self._loaded:
            return HealthReport(
                status="down",
                abi_version=ABI_VERSION,
                loaded=False,
                uptime_sec=0.0,
            )
        return HealthReport(
            status="ok",
            abi_version=ABI_VERSION,
            loaded=True,
            uptime_sec=time.time() - self._t0,
            details={"ctx_keys": sorted(self._ctx.keys())},
        )

    def capabilities(self) -> list[str]:
        return sorted(self._handlers.keys())

    def contracts(self) -> list[str]:
        return ["C00", "C82", "C83", "C84", "C85"]

    def register(self, name: str, handler: Callable[..., EvidenceOutput]) -> None:
        self._handlers[name] = handler

    def execute(
        self,
        capability: str,
        params: Mapping[str, Any] | None = None,
        nivel: str = "MID",
    ) -> EvidenceOutput:
        if not self._loaded:
            return EvidenceOutput(
                ok=False,
                capability=capability,
                evidence_hash="",
                error="extension_not_loaded",
            )
        h = self._handlers.get(capability)
        if h is None:
            return EvidenceOutput(
                ok=False,
                capability=capability,
                evidence_hash="",
                error=f"unknown_capability:{capability}",
            )
        return h(dict(params or {}), str(nivel).upper())

    # --- default capabilities ---

    def _cap_ping(self, params: dict[str, Any], nivel: str) -> EvidenceOutput:
        return EvidenceOutput(
            ok=True,
            capability="ping",
            evidence_hash="sha256:ping",
            data={"pong": True, "nivel": nivel},
        )

    def _cap_route_op(self, params: dict[str, Any], nivel: str) -> EvidenceOutput:
        from contract_engine.sentinela_router import route

        op = str(params.get("op_type") or "READ_LOCAL")
        decision = route(
            op_type=op,
            payload=params.get("payload"),
            path=params.get("path"),
            mount_mode=str(self._ctx.get("mount_mode") or "extension"),
            strict_reverse=bool(params.get("strict_reverse", False)),
        )
        return EvidenceOutput(
            ok=not decision.block_execution,
            capability="route_op",
            evidence_hash=decision.fingerprint_hash,
            set_hash=decision.set_hash,
            data=decision.to_dict(),
            error="blocked" if decision.block_execution else None,
        )

    def _cap_sheriff_gate(self, params: dict[str, Any], nivel: str) -> EvidenceOutput:
        from contract_engine.sentinela_router import route
        from sheriff.gate import run_sheriff

        op = str(params.get("op_type") or "READ_LOCAL")
        decision = route(
            op_type=op,
            payload=params.get("payload"),
            strict_reverse=False,
            mount_mode="extension",
        )
        verdict, _ = run_sheriff(decision.to_dict())
        return EvidenceOutput(
            ok=verdict.allow_execute,
            capability="sheriff_gate",
            evidence_hash=decision.fingerprint_hash,
            set_hash=decision.set_hash,
            sheriff_state=verdict.state.value,
            data=verdict.to_dict(),
            error=None if verdict.allow_execute else ";".join(verdict.reasons),
        )
