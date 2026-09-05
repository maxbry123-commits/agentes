from dataclasses import dataclass, field
from typing import Sequence

from .research import ResearchFinding
from .resolver import ResolvedRepository
from .skills import SkillRequirement


@dataclass(frozen=True)
class AgentContext:
    """Contexto acotado que se entrega al agente.

    Nunca se envía el repositorio completo.
    """
    objective: str
    selected_repositories: tuple[ResolvedRepository, ...]
    relevant_findings: tuple[ResearchFinding, ...]
    required_skills: tuple[SkillRequirement, ...]
    constraints: tuple[str, ...] = ()
    previous_failures: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


class ContextBuilder:
    """Construye un AgentContext a partir de findings resueltos."""

    def build(
        self,
        objective: str,
        findings: Sequence[ResearchFinding],
        resolved: Sequence[ResolvedRepository],
        skills: Sequence[SkillRequirement],
        constraints: Sequence[str] = (),
    ) -> AgentContext:
        return AgentContext(
            objective=objective,
            selected_repositories=tuple(resolved),
            relevant_findings=tuple(findings),
            required_skills=tuple(skills),
            constraints=tuple(constraints),
        )
