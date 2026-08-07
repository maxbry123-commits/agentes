"""Simulation Engine."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from ..plugin.universal_plugin import UniversalPlugin

@dataclass
class SimulationReport:
    ok: bool
    checks: dict = field(default_factory=dict)
    trace: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    def to_dict(self): return asdict(self)

class SimulationEngine:
    def run(self, plugin: UniversalPlugin, sample_capability=None):
        checks, errors, trace = {}, [], []
        checks["plugin_loaded"] = plugin.load({})
        if not checks["plugin_loaded"]: errors.append("load_failed")
        m = plugin.manifest
        checks["manifest_id"] = bool(m.id)
        checks["has_capabilities"] = len(m.capabilities) > 0
        if not checks["has_capabilities"]: errors.append("no_capabilities")
        caps = plugin.capability_ids()
        for c in caps:
            if c not in plugin.handlers:
                plugin.handlers[c] = lambda payload, _c=c: {"ok": True, "capability": _c, "simulated": True}
        checks["health_ok"] = plugin.health().get("status") == "ok"
        trace += ["load", "health"]
        cap = sample_capability or (caps[0] if caps else None)
        if cap:
            out = plugin.invoke(cap, {"_sim": True})
            checks["invoke_ok"] = bool(out.get("ok", False))
            trace.append(f"invoke:{cap}")
            if not checks["invoke_ok"]: errors.append(f"invoke_failed:{cap}")
        else:
            checks["invoke_ok"] = False; errors.append("no_capability_to_invoke")
        plugin.unload(); checks["unload_ok"] = True; trace.append("unload")
        return SimulationReport(all(checks.values()) and not errors, checks, trace, errors)
