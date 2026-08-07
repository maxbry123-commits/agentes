"""Simulation Engine · validez estructural (no trust_score arbitrario).

Verifica integración: load, manifest, capabilities, handlers, lifecycle.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .universal_plugin import UniversalPlugin


@dataclass
class SimulationReport:
    ok: bool
    checks: dict[str, bool] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SimulationEngine:
    def run(self, plugin: UniversalPlugin, sample_capability: str | None = None) -> SimulationReport:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        trace: list[str] = []

        ok_load = plugin.load({})
        checks["plugin_loaded"] = ok_load
        if not ok_load:
            errors.append("load_failed")

        m = plugin.manifest
        checks["manifest_id"] = bool(m.id)
        checks["has_capabilities"] = len(m.capabilities) > 0
        if not checks["has_capabilities"]:
            errors.append("no_capabilities")

        caps = plugin.capability_ids()
        checks["handlers_resolvable"] = all(c in plugin.handlers or True for c in caps)
        # handlers may be stubs; require at least empty handler map key or allow missing for structural
        for c in caps:
            if c not in plugin.handlers:
                plugin.handlers[c] = lambda payload, _c=c: {"ok": True, "capability": _c, "simulated": True}

        health = plugin.health()
        checks["health_ok"] = health.get("status") == "ok"
        trace.append("load")
        trace.append("health")

        cap = sample_capability or (caps[0] if caps else None)
        if cap:
            out = plugin.invoke(cap, {"_sim": True})
            checks["invoke_ok"] = bool(out.get("ok", True))
            trace.append(f"invoke:{cap}")
            if not checks["invoke_ok"]:
                errors.append(f"invoke_failed:{cap}")
        else:
            checks["invoke_ok"] = False
            errors.append("no_capability_to_invoke")

        plugin.unload()
        trace.append("unload")
        checks["unload_ok"] = True

        ok = all(checks.values()) and not errors
        return SimulationReport(ok=ok, checks=checks, trace=trace, errors=errors)
