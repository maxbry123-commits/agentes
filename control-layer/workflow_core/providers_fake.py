from dataclasses import dataclass
from typing import Sequence

from .research import ResearchFinding, ResearchRequest


@dataclass(frozen=True)
class FakeGitHubProvider:
    """Provider de prueba que simula resultados de GitHub.

    No hace llamadas de red. Solo para tests y dry-run.
    """

    def search(self, request: ResearchRequest, limit: int = 5) -> Sequence[ResearchFinding]:
        return tuple(
            ResearchFinding(
                finding_id=f"gh-{i}",
                source="github",
                url=f"https://github.com/example/repo-{i}",
                repository=f"example/repo-{i}",
                version="1.0.0",
                commit=f"abc{i:03d}",
                finding=f"Simulated finding for {request.objective}",
                evidence=(f"simulated-evidence-{i}",),
            )
            for i in range(min(limit, request.minimum_sources))
        )


@dataclass(frozen=True)
class FakePyPIProvider:
    """Provider de prueba que simula resultados de PyPI."""

    def search(self, request: ResearchRequest, limit: int = 5) -> Sequence[ResearchFinding]:
        return tuple(
            ResearchFinding(
                finding_id=f"pypi-{i}",
                source="pypi",
                url=f"https://pypi.org/project/example-pkg-{i}/",
                repository=None,
                version="0.1.0",
                commit=None,
                finding=f"Simulated PyPI package for {request.component}",
                evidence=(f"pypi-evidence-{i}",),
            )
            for i in range(min(limit, 3))
        )
