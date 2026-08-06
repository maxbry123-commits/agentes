from dataclasses import dataclass
from pathlib import Path

from .resolver import ResolvedRepository


@dataclass(frozen=True)
class MirrorRecord:
    repository: str
    local_path: str
    commit: str | None
    content_hash: str | None


class RepositoryMirror:
    """Registro de mirrors locales.

    No descarga todavía — solo define el contrato y el path determinista.
    La descarga real (git archive / tarball + SHA256) se implementa después.
    """

    def __init__(self, base_dir: str | Path = "workspace/repository-mirrors") -> None:
        self.base_dir = Path(base_dir)

    def path_for(self, resolved: ResolvedRepository, category: str = "workflow") -> Path:
        name = resolved.repository.replace("/", "__").replace(":", "_")
        return self.base_dir / category / name

    def register(self, resolved: ResolvedRepository, category: str = "workflow") -> MirrorRecord:
        local = self.path_for(resolved, category)
        return MirrorRecord(
            repository=resolved.repository,
            local_path=str(local),
            commit=resolved.commit,
            content_hash=resolved.content_hash,
        )
