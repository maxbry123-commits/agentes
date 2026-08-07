"""Evolution Engine v2 · Universal Plugin compiler.

Flujo: Source → IR → Authority → Policy → Placement → UniversalPlugin → Simulate → Register
"""
from .evo_ir import EvoIR, ComponentIR, CapabilityIR
from .authority import classify_authority, AuthorityNode, DEFAULT_POLICY
from .policy import TransformationPlan, build_plan, select_policy, POLICIES
from .placement import resolve_placement, Placement
from .universal_plugin import UniversalPlugin, PluginManifest, CapabilityContract
from .simulation import SimulationEngine, SimulationReport
from .compiler import EvolutionCompiler, CompileResult, EvolutionManifest
from .source_reuse import SourceReuseContract, SourceRef
from .sandbox_gate import SandboxGate, GateDecision

__all__ = [
    "EvoIR",
    "ComponentIR",
    "CapabilityIR",
    "classify_authority",
    "AuthorityNode",
    "DEFAULT_POLICY",
    "TransformationPlan",
    "build_plan",
    "select_policy",
    "POLICIES",
    "resolve_placement",
    "Placement",
    "UniversalPlugin",
    "PluginManifest",
    "CapabilityContract",
    "SimulationEngine",
    "SimulationReport",
    "EvolutionCompiler",
    "CompileResult",
    "EvolutionManifest",
    "SourceReuseContract",
    "SourceRef",
    "SandboxGate",
    "GateDecision",
]
