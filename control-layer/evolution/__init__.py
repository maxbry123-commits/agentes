"""Evolution Engine v3."""
from .controller import EvolutionController, EvolutionResult
from .registry.capability_registry import CapabilityRegistry
from .plugin.universal_plugin import UniversalPlugin, PluginManifest, CapabilityContract
from .evo_ir import EvoIR

__all__ = [
    "EvolutionController",
    "EvolutionResult",
    "CapabilityRegistry",
    "UniversalPlugin",
    "PluginManifest",
    "CapabilityContract",
    "EvoIR",
]
