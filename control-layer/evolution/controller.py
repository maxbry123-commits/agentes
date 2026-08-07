"""Evolution Controller · pipeline completo."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from .acquisition.license_auditor import LicenseAuditor
from .acquisition.source_store import SourceStore
from .analysis.architecture import ArchitectureAnalyzer
from .analysis.authority_graph import build_authority_graph
from .evo_ir import CapabilityIR, ComponentIR, EvoIR
from .planning.placement import resolve_placement
from .planning.policy_engine import build_plan
from .plugin.universal_plugin import CapabilityContract, PluginManifest, UniversalPlugin
from .registry.capability_registry import CapabilityRegistry
from .simulation.engine import SimulationEngine

@dataclass
class EvolutionResult:
    ok: bool
    phase: str
    evo_ir: dict = field(default_factory=dict)
    plan: dict = field(default_factory=dict)
    simulation: dict = field(default_factory=dict)
    placements: list = field(default_factory=list)
    registered: list = field(default_factory=list)
    plugin_id: str = ""
    error: str = ""
    license: dict = field(default_factory=dict)
    def to_dict(self):
        return {"ok": self.ok, "phase": self.phase, "plugin_id": self.plugin_id, "error": self.error, "license": self.license, "evo_ir": self.evo_ir, "plan": self.plan, "simulation": self.simulation, "placements": self.placements, "registered": self.registered}

class EvolutionController:
    def __init__(self, registry=None, sources_dir="evolution/sources"):
        self.license = LicenseAuditor()
        self.store = SourceStore(sources_dir)
        self.arch = ArchitectureAnalyzer()
        self.sim = SimulationEngine()
        self.registry = registry or CapabilityRegistry()

    def evolve_path(self, path, *, identity, source_type="agent", capabilities=None, repo_url="", ref="", allow_director_license=False, register=True):
        path = Path(path)
        lic = self.license.audit(path)
        if lic.veredicto == "STOP":
            return EvolutionResult(False, "LICENSE_STOP", error="license_stop", license=lic.to_dict())
        if lic.veredicto == "DIRECTOR" and not allow_director_license:
            return EvolutionResult(False, "LICENSE_DIRECTOR", error="license_requires_director", license=lic.to_dict())
        receipt = self.store.register_local(identity, path, ref=ref, repo_url=repo_url)
        amap = self.arch.analyze_path(receipt.path)
        edges = build_authority_graph(amap.components)
        edge_by = {e.component: e for e in edges}
        components = []
        for c in amap.components:
            name = str(c.get("name"))
            e = edge_by.get(name)
            components.append(ComponentIR(name=name, path=str(c.get("path") or ""), kind=str(c.get("kind") or ""), authority=e.authority if e else "unknown", action=e.action if e else "adapt", evidence=list(e.evidence) if e else [], confidence=e.confidence if e else 0.0, certainty=e.certainty if e else "UNKNOWN", side_effects=list(c.get("side_effects") or []), calls=list(c.get("calls") or c.get("methods") or [])[:20]))
        caps_in = list(capabilities or [])
        if not caps_in:
            if amap.fingerprint.get("has_code_gen"): caps_in += [f"{identity}.code.generate", f"{identity}.code.analyze"]
            if amap.fingerprint.get("has_tools"): caps_in.append(f"{identity}.tools.execute")
            if amap.fingerprint.get("has_git"): caps_in.append(f"{identity}.git.diff")
            if amap.fingerprint.get("has_browser"): caps_in.append(f"{identity}.browser.navigate")
            if amap.fingerprint.get("has_workflow"): caps_in += [f"{identity}.workflow.execute", f"{identity}.workflow.validate"]
            if not caps_in: caps_in = [f"{identity}.capability.default"]
        ir = EvoIR(identity=identity, source_type=source_type, source_path=receipt.path, source_repo=repo_url, source_ref=ref, source_sha256=receipt.sha256_tree, license_spdx=lic.spdx, license_verdict=lic.veredicto, components=components, capabilities=[CapabilityIR(id=c, origin=identity) for c in caps_in], fingerprint=amap.fingerprint, entrypoints=amap.entrypoints, side_effects=amap.side_effects, meta={"file_count": amap.file_count})
        plan = build_plan(ir)
        plugin_id = f"absorbed.{identity}".replace("/", ".")
        contracts = [CapabilityContract(id=cid, entrypoint=f"handlers.{cid.replace('.', '_')}", owner_plugin=plugin_id, provides=[cid]) for cid in plan.capabilities_out]
        placements = [resolve_placement(cid, identity).to_dict() for cid in plan.capabilities_out]
        domain = placements[0]["domain"] if placements else "integrations"
        ppath = placements[0]["path"] if placements else f"extensions/integrations/{identity}"
        manifest = PluginManifest(id=plugin_id, version="0.1.0", namespace=plugin_id, origin_type=source_type, source_repo=repo_url, source_ref=ref, source_sha256=receipt.sha256_tree, license_spdx=lic.spdx, capabilities=contracts, placement_domain=domain, placement_path=ppath, authority_notes={"preserved_cognitive": ",".join(plan.preserved_cognitive[:20]), "subordinated_control": ",".join(plan.subordinated_control[:20])}, meta={"strategy": plan.strategy, "policy_id": plan.policy_id})
        plugin = UniversalPlugin(manifest=manifest, handlers={})
        sim = self.sim.run(plugin, sample_capability=plan.capabilities_out[0] if plan.capabilities_out else None)
        if not sim.ok:
            return EvolutionResult(False, "SIMULATION_FAILED", evo_ir=ir.to_dict(), plan=plan.to_dict(), simulation=sim.to_dict(), placements=placements, plugin_id=plugin_id, error=";".join(sim.errors), license=lic.to_dict())
        registered = []
        if register:
            registered = self.registry.register_plugin(plugin, domain=domain)
            plugin.load({})
        return EvolutionResult(True, "REGISTERED" if register else "SIMULATED", evo_ir=ir.to_dict(), plan=plan.to_dict(), simulation=sim.to_dict(), placements=placements, registered=registered, plugin_id=plugin_id, license=lic.to_dict())
