"""Evolution Engine v3 · 100% núcleo operativo."""
from .controller import EvolutionControllerV2 as EvolutionController
from .controller import EvolutionControllerV2, EvolutionResult
from .registry.capability_registry import CapabilityRegistry
from .registry.capability_graph import CapabilityGraph
from .plugin.universal_plugin import UniversalPlugin, PluginManifest, CapabilityContract
from .evo_ir import EvoIR
from .skill.skill_compiler import SkillCompiler
from .events.absorb_bus import AbsorbBus

__all__ = [
    "EvolutionController",
    "EvolutionControllerV2",
    "EvolutionResult",
    "CapabilityRegistry",
    "CapabilityGraph",
    "UniversalPlugin",
    "PluginManifest",
    "CapabilityContract",
    "EvoIR",
    "SkillCompiler",
    "AbsorbBus",
]
