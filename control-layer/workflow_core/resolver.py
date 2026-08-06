from dataclasses import dataclass
from .research import ResearchFinding


@dataclass(frozen=True)
class ResolvedRepository:
    repository: str
    commit: str | None
    version: str | None
    source_url: str
    content_hash: str | None = None


class RepositoryResolver:
    """Resuelve un ResearchFinding a un repositorio fuente determinista.

    Nunca hace git clone main. Solo registra la información ya conocida
    en el finding para posterior mirror/download.
    """

    def resolve(self, finding: ResearchFinding) -> ResolvedRepository:
        if not finding.repository and not finding.url:
            raise ValueError(f"Finding {finding.finding_id} has no repository or url")

        return ResolvedRepository(
            repository=finding.repository or finding.url,
            commit=finding.commit,
            version=finding.version,
            source_url=finding.url,
            content_hash=None,  # se calcula en el paso de mirror/download
        )
