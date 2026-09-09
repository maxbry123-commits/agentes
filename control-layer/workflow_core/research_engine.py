from dataclasses import dataclass, field
from typing import Sequence

from .context import AgentContext, ContextBuilder
from .research import ResearchFinding, ResearchRequest
from .resolver import RepositoryResolver, ResolvedRepository
from .skills import SkillRequirement


@dataclass
class ResearchResult:
    request: ResearchRequest
    findings: tuple[ResearchFinding, ...]
    resolved: tuple[ResolvedRepository, ...]
    context: AgentContext
    complete: bool  # True solo si len(findings) >= minimum_sources


class ResearchEngine:
    """Motor mínimo de investigación.

    En esta fase solo orquesta contratos ya existentes.
    La obtención real de ≥20 fuentes queda para implementación posterior
    (providers reales de GitHub/PyPI/etc.).
    """

    def __init__(self) -> None:
        self.resolver = RepositoryResolver()
        self.context_builder = ContextBuilder()

    def run(
        self,
        request: ResearchRequest,
        findings: Sequence[ResearchFinding],
        skills: Sequence[SkillRequirement] = (),
    ) -> ResearchResult:
        resolved = tuple(self.resolver.resolve(f) for f in findings)
        context = self.context_builder.build(
            objective=request.objective,
            findings=findings,
            resolved=resolved,
            skills=skills,
        )
        complete = len(findings) >= request.minimum_sources
        return ResearchResult(
            request=request,
            findings=tuple(findings),
            resolved=resolved,
            context=context,
            complete=complete,
        )
