import hashlib
import urllib.request
from pathlib import Path

from .mirror import MirrorRecord, RepositoryMirror
from .resolver import ResolvedRepository


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_tarball(url: str, dest: Path) -> str:
    """Descarga determinista de un tarball y devuelve el SHA256."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    return sha256_of_file(dest)


class DeterministicDownloader:
    """Realiza la descarga real y actualiza el MirrorRecord con content_hash."""

    def __init__(self, mirror: RepositoryMirror | None = None) -> None:
        self.mirror = mirror or RepositoryMirror()

    def download(self, resolved: ResolvedRepository, tarball_url: str, category: str = "workflow") -> MirrorRecord:
        local_dir = self.mirror.path_for(resolved, category)
        tarball_path = local_dir / "source.tar.gz"
        content_hash = download_tarball(tarball_url, tarball_path)
        return MirrorRecord(
            repository=resolved.repository,
            local_path=str(local_dir),
            commit=resolved.commit,
            content_hash=content_hash,
        )
