"""Evolution Engine · 5 modos · nunca source→prod."""
from .pipeline import EvolutionPipeline, EvolutionPhase, EvolutionRequest, EvolutionResult, EvolutionMode
from .source_reuse import SourceReuseContract, SourceRef
from .sandbox_gate import SandboxGate, GateDecision
from .factory import build_default_pipeline

__all__ = [
    "EvolutionPipeline",
    "EvolutionPhase",
    "EvolutionRequest",
    "EvolutionResult",
    "EvolutionMode",
    "SourceReuseContract",
    "SourceRef",
    "SandboxGate",
    "GateDecision",
    "build_default_pipeline",
]
