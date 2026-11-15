"""DUAL.02 — Package Montable ABI v1.0 (ejecutable)
Wordflow Extension ABI — montable sin tocar kernel.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional
import hashlib
import json
import time


@dataclass
class EvidenceOutput:
    ok: bool
    capability: str
    evidence_hash: str
    data: dict = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class ExtensionABI:
    """Contrato mínimo de montaje de extensiones."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[..., EvidenceOutput]] = {}
        self._mounted = False
        self._t0 = 0.0

    def register(self, capability_id: str, handler: Callable[..., EvidenceOutput]) -> None:
        if not capability_id or not callable(handler):
            raise ValueError("capability_id and handler required")
        self._handlers[capability_id] = handler

    def unregister(self, capability_id: str) -> None:
        self._handlers.pop(capability_id, None)

    def list_capabilities(self) -> List[str]:
        return sorted(self._handlers.keys())

    def execute(self, capability_id: str, params: dict | None = None) -> EvidenceOutput:
        if not self._mounted:
            return EvidenceOutput(
                ok=False,
                capability=capability_id,
                evidence_hash="",
                error="extension_not_mounted",
            )
        handler = self._handlers.get(capability_id)
        if handler is None:
            return EvidenceOutput(
                ok=False,
                capability=capability_id,
                evidence_hash="",
                error=f"unknown_capability:{capability_id}",
            )
        try:
            result = handler(params or {})
            if not isinstance(result, EvidenceOutput):
                raise TypeError("handler must return EvidenceOutput")
            return result
        except Exception as e:
            return EvidenceOutput(
                ok=False,
                capability=capability_id,
                evidence_hash="",
                error=str(e),
            )

    def _mark_mounted(self) -> None:
        self._mounted = True
        self._t0 = time.time()


def _hash_evidence(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def attach_to_wordflow_extension(ext: ExtensionABI) -> ExtensionABI:
    """Única vía de montaje. Kernel nunca importa código de extensión directamente."""
    if not isinstance(ext, ExtensionABI):
        raise TypeError("ext must be ExtensionABI instance")

    # Default capability de prueba
    def _cap_ping(params: dict) -> EvidenceOutput:
        data = {"pong": True, "params": params}
        return EvidenceOutput(
            ok=True,
            capability="ping",
            evidence_hash=_hash_evidence(data),
            data=data,
        )

    if "ping" not in ext.list_capabilities():
        ext.register("ping", _cap_ping)

    ext._mark_mounted()
    return ext


if __name__ == "__main__":
    abi = ExtensionABI()
    abi = attach_to_wordflow_extension(abi)
    print("ABI mounted", abi.list_capabilities())
    print(abi.execute("ping", {"x": 1}).to_dict())
