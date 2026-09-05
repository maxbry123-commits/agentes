from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchRequest:
    research_id: str
    objective: str
    component: str
    minimum_sources: int = 20
    required_source_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchFinding:
    finding_id: str
    source: str
    url: str
    repository: str | None
    version: str | None
    commit: str | None
    finding: str
    evidence: tuple[str, ...] = ()
