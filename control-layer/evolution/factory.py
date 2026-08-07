"""Pipeline con 5 modos."""
from __future__ import annotations

from .pipeline import EvolutionPipeline
from .source_reuse import SourceReuseContract
from .sandbox_gate import SandboxGate
from .modes.agent_absorb import ModeAgentAbsorb
from .modes.decapitate import ModeDecapitate
from .modes.skill_compile import ModeSkillCompile
from .modes.os_source import ModeOsSource
from .modes.dataset import ModeDataset


def build_default_pipeline(reuse: SourceReuseContract | None = None) -> EvolutionPipeline:
    pipe = EvolutionPipeline(reuse=reuse or SourceReuseContract(), gate=SandboxGate())
    for h in (ModeAgentAbsorb(), ModeDecapitate(), ModeSkillCompile(), ModeOsSource(), ModeDataset()):
        pipe.register_handler(h)
    return pipe
