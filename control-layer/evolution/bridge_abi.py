"""Puente UniversalPlugin ↔ extension.abi + research/opportunity/watchdog."""
from __future__ import annotations
from typing import Any
from .plugin.universal_plugin import UniversalPlugin
from .registry.capability_registry import CapabilityRegistry
try:
    from extension.abi import EvidenceOutput
except ImportError:
    EvidenceOutput = None  # type: ignore

def mount_plugin_on_extension(ext, plugin):
    mounted = []
    if not hasattr(ext, "register"):
        return mounted
    def _make_handler(cap_id, plug):
        def _handler(params, nivel="MID"):
            if not plug._loaded:
                plug.load({})
            out = plug.invoke(cap_id, params)
            if EvidenceOutput is None:
                return out
            return EvidenceOutput(ok=bool(out.get("ok", False)), capability=cap_id, evidence_hash=f"sha256:evo:{cap_id}", data=dict(out), error=out.get("error"))
        return _handler
    for cap in plugin.capability_ids():
        ext.register(cap, _make_handler(cap, plugin))
        mounted.append(cap)
    return mounted

def mount_registry_on_extension(ext, registry):
    all_mounted = []
    for plugin in list(registry._plugins.values()):
        all_mounted.extend(mount_plugin_on_extension(ext, plugin))
    return all_mounted

class EvolutionExtensionService:
    def __init__(self, sources_dir="evolution/sources", extensions_dir="extensions"):
        from .controller import EvolutionControllerV2
        self.controller = EvolutionControllerV2(sources_dir=sources_dir, extensions_dir=extensions_dir)
        self.registry = self.controller.registry
        self.graph = self.controller.graph

    def evolve(self, **kwargs):
        path = kwargs.get("path") or None
        r = self.controller.evolve_path(path, identity=str(kwargs.get("identity") or "unknown"), source_type=str(kwargs.get("source_type") or "agent"), repo_url=str(kwargs.get("repo_url") or ""), ref=str(kwargs.get("ref") or "main"), expected_tree_sha256=str(kwargs.get("expected_tree_sha256") or ""), allow_director_license=bool(kwargs.get("allow_director_license", False)), register=True, write_package=True)
        self.controller.watchdog.on_evolve_result(r.to_dict())
        return r.to_dict()

    def evolve_skill(self, **kwargs):
        return self.controller.evolve_skill(**kwargs)

    def research(self, **kwargs):
        return {"ok": True, "candidates": self.controller.research(str(kwargs.get("query") or ""), local=kwargs.get("local"))}

    def research_and_evolve(self, **kwargs):
        results = self.controller.research_and_evolve(str(kwargs.get("query") or ""), local=kwargs.get("local"))
        return {"ok": all(r.get("ok") for r in results) if results else False, "results": results}

    def opportunities(self, **kwargs):
        return {"ok": True, "opportunities": self.controller.scan_opportunities(kwargs.get("task_hints") or [])}

    def safe_invoke(self, **kwargs):
        return self.controller.safe_invoke(str(kwargs.get("capability") or ""), kwargs.get("payload"))

    def watchdog_status(self, **kwargs):
        return {"ok": True, **self.controller.watchdog.to_dict()}

    def attach_to_wordflow_extension(self, ext):
        mounted = mount_registry_on_extension(ext, self.registry)
        def _wrap(name, fn):
            def _handler(params, nivel="MID"):
                result = fn(**params)
                if name == "evolution.evolve":
                    mount_registry_on_extension(ext, self.registry)
                if EvidenceOutput is None:
                    return result
                ok = bool(result.get("ok", True)) if isinstance(result, dict) else True
                return EvidenceOutput(ok=ok, capability=name, evidence_hash=f"sha256:{name}", data=result if isinstance(result, dict) else {"result": result}, error=(result.get("error") if isinstance(result, dict) else None))
            return _handler
        if hasattr(ext, "register"):
            for name, fn in {
                "evolution.evolve": self.evolve,
                "evolution.skill_compile": self.evolve_skill,
                "evolution.research": self.research,
                "evolution.research_and_evolve": self.research_and_evolve,
                "evolution.opportunities": self.opportunities,
                "evolution.safe_invoke": self.safe_invoke,
                "evolution.watchdog": self.watchdog_status,
            }.items():
                ext.register(name, _wrap(name, fn))
                mounted.append(name)
        return mounted
