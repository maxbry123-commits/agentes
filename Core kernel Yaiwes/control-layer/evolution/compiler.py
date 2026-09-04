"""Evolution Compiler · SOURCE → EVO-IR → Plan → UniversalPlugin.

Determinista por defecto. LLM solo como Semantic Resolver (no implementado aquí).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .authority import AuthorityNode, classify_authority
from .evo_ir import CapabilityIR, ComponentIR, EvoIR
from .placement import resolve_placement
from .policy import TransformationPlan, build_plan
from .simulation import SimulationEngine, SimulationReport
from .universal_plugin import CapabilityContract, PluginManifest, UniversalPlugin


@dataclass
class EvolutionManifest:
    """Receta reproducible de una evolución."""

    source: dict[str, Any]
    target_namespace: str
    architecture: dict[str, Any]
    transformation: dict[str, Any]
    capabilities: list[str]
    removed: list[str]
    retained: list[str]
    kernel_binding: str = "UniversalPlugin"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target_namespace": self.target_namespace,
            "architecture": self.architecture,
            "transformation": self.transformation,
            "capabilities": self.capabilities,
            "removed": self.removed,
            "retained": self.retained,
            "kernel_binding": self.kernel_binding,
        }


@dataclass
class CompileResult:
    ok: bool
    plugin: UniversalPlugin | None
    evo_ir: EvoIR | None
    plan: TransformationPlan | None
    evolution_manifest: EvolutionManifest | None
    simulation: SimulationReport | None
    placements: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "error": self.error,
            "evo_ir": self.evo_ir.to_dict() if self.evo_ir else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "evolution_manifest": self.evolution_manifest.to_dict() if self.evolution_manifest else None,
            "simulation": self.simulation.to_dict() if self.simulation else None,
            "placements": self.placements,
            "plugin_id": self.plugin.manifest.id if self.plugin else None,
        }


class EvolutionCompiler:
    """Núcleo: clasifica, analiza autoridad, planifica, genera plugin, simula."""

    def __init__(self) -> None:
        self.sim = SimulationEngine()

    def build_ir_from_hints(
        self,
        *,
        identity: str,
        source_type: str,
        components: list[dict[str, Any]],
        capabilities: list[str],
        fingerprint: dict[str, bool] | None = None,
        source_repo: str = "",
        source_ref: str = "",
        source_sha256: str = "",
    ) -> EvoIR:
        comps: list[ComponentIR] = []
        for c in components:
            name = str(c.get("name") or c)
            side = list(c.get("side_effects") or [])
            calls = list(c.get("calls") or [])
            node = classify_authority(name, side, calls)
            comps.append(
                ComponentIR(
                    name=name,
                    path=str(c.get("path") or ""),
                    kind_hint=str(c.get("kind") or ""),
                    authority=node.authority,
                    reusable=node.action != "subordinate",
                    evidence=node.evidence,
                    confidence=node.confidence,
                    side_effects=side,
                )
            )
        caps = [
            CapabilityIR(id=cid, authority="execution", action="adapt")
            for cid in capabilities
        ]
        fp = dict(fingerprint or {})
        return EvoIR(
            identity=identity,
            source_type=source_type,
            source_repo=source_repo,
            source_ref=source_ref,
            source_sha256=source_sha256,
            components=comps,
            capabilities=caps,
            fingerprint=fp,
            decision_layer_detected=fp.get("has_agent_loop", False),
            execution_layer_detected=fp.get("has_tools", False),
            memory_layer_detected=fp.get("has_memory", False),
        )

    def compile_ir(self, ir: EvoIR) -> CompileResult:
        nodes: list[AuthorityNode] = [
            classify_authority(c.name, c.side_effects, c.evidence) for c in ir.components
        ]
        # prefer authority already on component if certain
        for i, c in enumerate(ir.components):
            if c.confidence >= 0.7:
                nodes[i] = AuthorityNode(c.name, c.authority, c.authority and "preserve" or "adapt", c.evidence, c.confidence)
                from .authority import DEFAULT_POLICY

                nodes[i].action = DEFAULT_POLICY.get(c.authority, "adapt")
                if c.authority == "cognitive":
                    nodes[i].action = "preserve"
                if c.authority == "control":
                    nodes[i].action = "subordinate"

        plan = build_plan(ir, nodes)
        if plan.strategy == "reject":
            return CompileResult(False, None, ir, plan, None, None, error="rejected_by_policy")

        plugin_id = f"absorbed.{ir.identity}".replace("/", ".")
        contracts = [
            CapabilityContract(id=cid, entrypoint=f"handlers.{cid.replace('.', '_')}")
            for cid in plan.capabilities_out
        ]
        placements = []
        for cid in plan.capabilities_out:
            pl = resolve_placement(cid, ir.identity)
            placements.append(pl.to_dict())

        domain = placements[0]["domain"] if placements else "integrations"
        path = placements[0]["path"] if placements else f"extensions/integrations/{ir.identity}"

        manifest = PluginManifest(
            id=plugin_id,
            version="0.1.0",
            namespace=plugin_id,
            origin_type=ir.source_type,
            source_repo=ir.source_repo,
            source_ref=ir.source_ref,
            source_sha256=ir.source_sha256,
            capabilities=contracts,
            placement_domain=domain,
            placement_path=path,
            authority_notes={
                "preserved_cognitive": ",".join(plan.preserved_cognitive),
                "subordinated_control": ",".join(plan.removed_control),
            },
        )
        plugin = UniversalPlugin(manifest=manifest, handlers={})

        evo_man = EvolutionManifest(
            source={
                "type": ir.source_type,
                "name": ir.identity,
                "repository": ir.source_repo,
                "revision": ir.source_ref,
                "sha256": ir.source_sha256,
            },
            target_namespace=plugin_id,
            architecture={
                "decision_layer": ir.decision_layer_detected,
                "execution_layer": ir.execution_layer_detected,
                "memory_layer": ir.memory_layer_detected,
                "fingerprint": ir.fingerprint,
            },
            transformation=plan.to_dict(),
            capabilities=list(plan.capabilities_out),
            removed=list(plan.removed_control),
            retained=list(plan.preserved_cognitive),
        )

        sim = self.sim.run(plugin, sample_capability=plan.capabilities_out[0] if plan.capabilities_out else None)
        ok = sim.ok
        return CompileResult(
            ok=ok,
            plugin=plugin,
            evo_ir=ir,
            plan=plan,
            evolution_manifest=evo_man,
            simulation=sim,
            placements=placements,
            error="" if ok else ";".join(sim.errors),
        )
