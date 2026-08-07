"""Puente UniversalPlugin ↔ extension.abi."""
from __future__ import annotations
from typing import Any
from .plugin.universal_plugin import UniversalPlugin
from .registry.capability_registry import CapabilityRegistry

try:
    from extension.abi import EvidenceOutput
except ImportError:
    EvidenceOutput = None  # type: ignore

def mount_plugin_on_extension(ext, plugin: UniversalPlugin):
    mounted = []
    if not hasattr(ext, "register"): return mounted
    def _make_handler(cap_id, plug):
        def _handler(params, nivel="MID"):
            if not plug._loaded: plug.load({})
            out = plug.invoke(cap_id, params)
            if EvidenceOutput is None: return out
            return EvidenceOutput(ok=bool(out.get("ok", False)), capability=cap_id, evidence_hash=f"sha256:evo:{cap_id}", data=dict(out), error=out.get("error"))
        return _handler
    for cap in plugin.capability_ids():
        ext.register(cap, _make_handler(cap, plugin))
        mounted.append(cap)
    return mounted

def mount_registry_on_extension(ext, registry: CapabilityRegistry):
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
        r = self.controller.evolve_path(
            path,
            identity=str(kwargs.get("identity") or "unknown"),
            source_type=str(kwargs.get("source_type") or "agent"),
            repo_url=str(kwargs.get("repo_url") or ""),
            ref=str(kwargs.get("ref") or "main"),
            expected_tree_sha256=str(kwargs.get("expected_tree_sha256") or ""),
            allow_director_license=bool(kwargs.get("allow_director_license", False)),
            register=True,
            write_package=True,
        )
        return r.to_dict()

    def evolve_skill(self, **kwargs):
        return self.controller.evolve_skill(**kwargs)

    def attach_to_wordflow_extension(self, ext):
        mounted = mount_registry_on_extension(ext, self.registry)
        def _evolve_handler(params, nivel="MID"):
            result = self.evolve(**params)
            mount_registry_on_extension(ext, self.registry)
            if EvidenceOutput is None: return result
            return EvidenceOutput(ok=bool(result.get("ok")), capability="evolution.evolve", evidence_hash=f"sha256:evolve:{result.get('plugin_id')}", data=result, error=result.get("error") or None)
        def _skill_handler(params, nivel="MID"):
            result = self.evolve_skill(skill_id=str(params.get("skill_id") or "skill"), steps=params.get("steps"), skill_text=str(params.get("skill_text") or ""))
            if EvidenceOutput is None: return result
            return EvidenceOutput(ok=bool(result.get("ok")), capability="evolution.skill_compile", evidence_hash=f"sha256:skill:{params.get('skill_id')}", data=result, error=result.get("error") or None)
        if hasattr(ext, "register"):
            ext.register("evolution.evolve", _evolve_handler)
            ext.register("evolution.skill_compile", _skill_handler)
            mounted += ["evolution.evolve", "evolution.skill_compile"]
        return mounted
