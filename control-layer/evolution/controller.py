"""Evolution Controller v2 · 100% núcleo operativo.

Pipeline:
  license → (git|local) acquire → AST/arch/authority → EVO-IR → policy
  → placement → UniversalPlugin → simulate → write package → ledger
  → registry + graph → events → ABI-ready
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .acquisition.git_acquire import GitAcquire
from .acquisition.license_auditor import LicenseAuditor
from .acquisition.source_store import SourceStore
from .analysis.architecture import ArchitectureAnalyzer
from .analysis.authority_graph import build_authority_graph
from .disk.package_writer import PackageWriter
from .events.absorb_bus import AbsorbBus
from .evo_ir import CapabilityIR, ComponentIR, EvoIR
from .ledger.evolution_ledger import EvolutionLedger, LedgerEntry
from .planning.placement import resolve_placement
from .planning.policy_engine import build_plan
from .plugin.universal_plugin import CapabilityContract, PluginManifest, UniversalPlugin
from .registry.capability_graph import CapabilityGraph
from .registry.capability_registry import CapabilityRegistry
from .simulation.engine import SimulationEngine
from .skill.skill_compiler import SkillCompiler


@dataclass
class EvolutionResult:
    ok: bool
    phase: str
    plugin_id: str = ""
    package_path: str = ""
    mutation_id: str = ""
    registered: list[str] = field(default_factory=list)
    evo_ir: dict[str, Any] = field(default_factory=dict)
    plan: dict[str, Any] = field(default_factory=dict)
    simulation: dict[str, Any] = field(default_factory=dict)
    placements: list[dict[str, Any]] = field(default_factory=list)
    license: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "phase": self.phase,
            "plugin_id": self.plugin_id,
            "package_path": self.package_path,
            "mutation_id": self.mutation_id,
            "registered": self.registered,
            "evo_ir": self.evo_ir,
            "plan": self.plan,
            "simulation": self.simulation,
            "placements": self.placements,
            "license": self.license,
            "events": self.events,
            "error": self.error,
        }


class EvolutionControllerV2:
    def __init__(
        self,
        *,
        sources_dir: str = "evolution/sources",
        extensions_dir: str = "extensions",
        ledger_path: str = "evolution/ledger.jsonl",
    ) -> None:
        self.license = LicenseAuditor()
        self.store = SourceStore(sources_dir)
        self.git = GitAcquire(sources_dir)
        self.arch = ArchitectureAnalyzer()
        self.sim = SimulationEngine()
        self.registry = CapabilityRegistry()
        self.graph = CapabilityGraph()
        self.writer = PackageWriter(extensions_dir)
        self.ledger = EvolutionLedger(ledger_path)
        self.bus = AbsorbBus()
        self.skills = SkillCompiler()
        self.extensions_dir = extensions_dir

    def evolve_path(
        self,
        path: str | Path | None = None,
        *,
        identity: str,
        source_type: str = "agent",
        capabilities: list[str] | None = None,
        repo_url: str = "",
        ref: str = "main",
        expected_tree_sha256: str = "",
        allow_director_license: bool = False,
        register: bool = True,
        write_package: bool = True,
    ) -> EvolutionResult:
        self.bus.emit("absorb.started", {"identity": identity, "source_type": source_type})

        if repo_url and not path:
            acq = self.git.acquire(
                repo_url=repo_url, ref=ref, dest_id=identity, expected_tree_sha256=expected_tree_sha256
            )
            if not acq.ok:
                self.bus.emit("absorb.failed", {"error": acq.error})
                return EvolutionResult(False, "GIT_ACQUIRE_FAILED", error=acq.error)
            local_path = Path(acq.path)
            self.bus.emit("absorb.scouted", {"path": acq.path, "commit": acq.commit})
        elif path:
            local_path = Path(path)
            receipt = self.store.register_local(identity, local_path, ref=ref, repo_url=repo_url)
            local_path = Path(receipt.path)
            self.bus.emit("absorb.scouted", {"path": str(local_path)})
        else:
            return EvolutionResult(False, "NO_SOURCE", error="path_or_repo_required")

        lic = self.license.audit(local_path)
        if lic.veredicto == "STOP":
            self.bus.emit("absorb.failed", {"error": "license_stop"})
            return EvolutionResult(False, "LICENSE_STOP", error="license_stop", license=lic.to_dict())
        if lic.veredicto == "DIRECTOR" and not allow_director_license:
            return EvolutionResult(
                False, "LICENSE_DIRECTOR", error="license_requires_director", license=lic.to_dict()
            )

        amap = self.arch.analyze_path(local_path)
        edges = build_authority_graph(amap.components)
        edge_by = {e.component: e for e in edges}
        components: list[ComponentIR] = []
        for c in amap.components:
            name = str(c.get("name"))
            e = edge_by.get(name)
            components.append(
                ComponentIR(
                    name=name,
                    path=str(c.get("path") or ""),
                    kind=str(c.get("kind") or ""),
                    authority=e.authority if e else "unknown",
                    action=e.action if e else "adapt",
                    evidence=list(e.evidence) if e else [],
                    confidence=e.confidence if e else 0.0,
                    certainty=e.certainty if e else "UNKNOWN",
                    side_effects=list(c.get("side_effects") or []),
                    calls=list(c.get("calls") or c.get("methods") or [])[:20],
                )
            )

        caps_in = list(capabilities or [])
        if not caps_in:
            if amap.fingerprint.get("has_code_gen"):
                caps_in += [f"{identity}.code.generate", f"{identity}.code.analyze"]
            if amap.fingerprint.get("has_tools"):
                caps_in.append(f"{identity}.tools.execute")
            if amap.fingerprint.get("has_git"):
                caps_in.append(f"{identity}.git.diff")
            if amap.fingerprint.get("has_browser"):
                caps_in.append(f"{identity}.browser.navigate")
            if amap.fingerprint.get("has_workflow"):
                caps_in += [f"{identity}.workflow.execute", f"{identity}.workflow.validate"]
            if not caps_in:
                caps_in = [f"{identity}.capability.default"]

        sha = ""
        receipt_file = local_path / "SOURCE_RECEIPT.json"
        if receipt_file.exists():
            import json

            try:
                data = json.loads(receipt_file.read_text())
                sha = data.get("sha256_tree") or data.get("tree_sha256") or ""
            except Exception:
                sha = ""

        ir = EvoIR(
            identity=identity,
            source_type=source_type,
            source_path=str(local_path),
            source_repo=repo_url,
            source_ref=ref,
            source_sha256=sha,
            license_spdx=lic.spdx,
            license_verdict=lic.veredicto,
            components=components,
            capabilities=[CapabilityIR(id=c, origin=identity) for c in caps_in],
            fingerprint=amap.fingerprint,
            entrypoints=amap.entrypoints,
            side_effects=amap.side_effects,
            meta={"file_count": amap.file_count},
        )
        self.bus.emit("absorb.pieces", {"count": len(components), "caps": caps_in})

        plan = build_plan(ir)
        plugin_id = f"absorbed.{identity}".replace("/", ".")
        contracts = [
            CapabilityContract(
                id=cid,
                entrypoint=f"handlers.{cid.replace('.', '_')}",
                owner_plugin=plugin_id,
                provides=[cid],
                requires=[],
            )
            for cid in plan.capabilities_out
        ]
        placements = [resolve_placement(cid, identity).to_dict() for cid in plan.capabilities_out]
        domain = placements[0]["domain"] if placements else "integrations"
        ppath = placements[0]["path"] if placements else f"extensions/integrations/{identity}"

        manifest = PluginManifest(
            id=plugin_id,
            version="0.1.0",
            namespace=plugin_id,
            origin_type=source_type,
            source_repo=repo_url,
            source_ref=ref,
            source_sha256=sha,
            license_spdx=lic.spdx,
            capabilities=contracts,
            placement_domain=domain,
            placement_path=ppath,
            authority_notes={
                "preserved_cognitive": ",".join(plan.preserved_cognitive[:20]),
                "subordinated_control": ",".join(plan.subordinated_control[:20]),
            },
            meta={"strategy": plan.strategy, "policy_id": plan.policy_id},
        )
        plugin = UniversalPlugin(manifest=manifest, handlers={})

        sim = self.sim.run(
            plugin, sample_capability=plan.capabilities_out[0] if plan.capabilities_out else None
        )
        self.bus.emit("absorb.tested", sim.to_dict())
        if not sim.ok:
            self.bus.emit("absorb.failed", {"error": sim.errors})
            return EvolutionResult(
                False,
                "SIMULATION_FAILED",
                plugin_id=plugin_id,
                evo_ir=ir.to_dict(),
                plan=plan.to_dict(),
                simulation=sim.to_dict(),
                placements=placements,
                license=lic.to_dict(),
                error=";".join(sim.errors),
                events=[e.to_dict() for e in self.bus.history],
            )

        package_path = ""
        if write_package:
            out = self.writer.write(
                plugin_id=plugin_id,
                domain=domain,
                placement_path=ppath,
                manifest=manifest.to_dict(),
                plan=plan.to_dict(),
                evo_ir=ir.to_dict(),
                simulation=sim.to_dict(),
            )
            package_path = str(out)
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location(f"evo_pkg_{identity}", out / "adapter.py")
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    plugin.handlers = dict(getattr(mod, "HANDLERS", {}))
            except Exception:
                pass
            self.bus.emit("absorb.pushed", {"package_path": package_path})

        mutation_id = self.ledger.next_id()
        self.ledger.append(
            LedgerEntry(
                mutation_id=mutation_id,
                plugin_id=plugin_id,
                source_path=str(local_path),
                package_path=package_path,
                strategy=plan.strategy,
                timestamp=__import__("time").time(),
                meta={"identity": identity},
            )
        )

        registered: list[str] = []
        if register:
            registered = self.registry.register_plugin(plugin, domain=domain)
            for c in contracts:
                self.graph.add_from_contract(c.to_dict(), plugin_id)
            plugin.load({})
            self.bus.emit("absorb.registered", {"capabilities": registered})

        return EvolutionResult(
            True,
            "REGISTERED" if register else "PACKAGED",
            plugin_id=plugin_id,
            package_path=package_path,
            mutation_id=mutation_id,
            registered=registered,
            evo_ir=ir.to_dict(),
            plan=plan.to_dict(),
            simulation=sim.to_dict(),
            placements=placements,
            license=lic.to_dict(),
            events=[e.to_dict() for e in self.bus.history],
        )

    def evolve_skill(
        self,
        *,
        skill_id: str,
        steps: list[Any] | None = None,
        skill_text: str = "",
    ) -> dict[str, Any]:
        self.bus.emit("absorb.started", {"identity": skill_id, "source_type": "skill"})
        r = self.skills.compile(
            skill_id=skill_id,
            steps=steps,
            skill_text=skill_text,
            out_dir=str(Path(self.extensions_dir) / "skills"),
        )
        if r.ok:
            pid = f"skill.{skill_id}"
            cap = f"skill.{skill_id}.run"
            plugin = UniversalPlugin(
                manifest=PluginManifest(
                    id=pid,
                    version="0.1.0",
                    namespace=pid,
                    origin_type="skill",
                    capabilities=[CapabilityContract(id=cap, provides=[cap], owner_plugin=pid)],
                    placement_domain="skills",
                    placement_path=str(Path(self.extensions_dir) / "skills" / skill_id),
                ),
                handlers={cap: lambda p, _c=cap: {"ok": True, "capability": _c, "dag": r.dag_path}},
            )
            self.registry.register_plugin(plugin, domain="skills")
            self.graph.add_from_contract({"id": cap, "provides": [cap]}, pid)
            self.bus.emit("absorb.registered", {"capabilities": [cap]})
        return r.to_dict()


# backward alias
EvolutionController = EvolutionControllerV2
