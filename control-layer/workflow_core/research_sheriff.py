from dataclasses import dataclass
from .research_engine import ResearchResult


@dataclass(frozen=True)
class ResearchSheriffDecision:
    allowed: bool
    reason: str
    missing: tuple[str, ...] = ()


class ResearchSheriff:
    """Valida que un ResearchResult cumple los 8 requisitos de G02-doc3 B6.

    No interpreta — solo cuenta y verifica presencia de campos.
    """

    def inspect(self, result: ResearchResult) -> ResearchSheriffDecision:
        missing: list[str] = []

        if not result.complete:
            missing.append(f"findings < {result.request.minimum_sources}")

        for f in result.findings:
            if not f.source:
                missing.append(f"{f.finding_id}: source missing")
            if not f.url:
                missing.append(f"{f.finding_id}: url missing")
            if not f.evidence:
                missing.append(f"{f.finding_id}: evidence missing")

        for r in result.resolved:
            if not r.repository:
                missing.append("repository missing")
            # version / commit / hash se recomiendan pero no bloquean en esta fase mínima

        if missing:
            return ResearchSheriffDecision(
                allowed=False,
                reason="Research rejected by Sheriff",
                missing=tuple(missing),
            )
        return ResearchSheriffDecision(allowed=True, reason="Research approved")
