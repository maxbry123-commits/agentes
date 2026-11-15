"""Universal Plugin · único contrato hacia el kernel.

REGLA: ningún componente externo se integra directo al kernel.
Todo lo evolucionado TERMINA como UniversalPlugin (+ UCC).
Compatible con extension/abi.py (load/unload/health/capabilities/execute).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping


@dataclass
class CapabilityContract:
    """UCC — Universal Capability Contract."""

    id: str
    version: str = "1.0.0"
    input_schema: str = ""
    output_schema: str = ""
    requires: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    permissions: dict[str, str] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    triggers: list[str] = field(default_factory=list)
    entrypoint: str = ""
    isolation: str = "none"  # none | sandbox | harness

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PluginManifest:
    id: str
    version: str
    namespace: str
    origin_type: str  # agent | software | skill | dataset | adapter | plugin
    source_repo: str = ""
    source_ref: str = ""
    source_sha256: str = ""
    capabilities: list[CapabilityContract] = field(default_factory=list)
    lifecycle: list[str] = field(default_factory=lambda: ["load", "health", "execute", "unload"])
    permissions: dict[str, str] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    placement_domain: str = "integrations"
    placement_path: str = ""
    authority_notes: dict[str, str] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["capabilities"] = [c.to_dict() if hasattr(c, "to_dict") else c for c in self.capabilities]
        return d


@dataclass
class UniversalPlugin:
    """Instancia montable. Kernel solo llama invoke/load/health."""

    manifest: PluginManifest
    handlers: dict[str, Callable[..., dict[str, Any]]] = field(default_factory=dict)
    _loaded: bool = False

    def load(self, ctx: Mapping[str, Any] | None = None) -> bool:
        self._loaded = True
        return True

    def unload(self) -> None:
        self._loaded = False

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok" if self._loaded else "down",
            "plugin_id": self.manifest.id,
            "capabilities": [c.id for c in self.manifest.capabilities],
        }

    def capability_ids(self) -> list[str]:
        return [c.id for c in self.manifest.capabilities]

    def invoke(self, capability: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if not self._loaded:
            return {"ok": False, "error": "plugin_not_loaded"}
        h = self.handlers.get(capability)
        if h is None:
            return {"ok": False, "error": f"unknown_capability:{capability}"}
        return h(dict(payload or {}))

    def to_dict(self) -> dict[str, Any]:
        return {"manifest": self.manifest.to_dict(), "loaded": self._loaded}
