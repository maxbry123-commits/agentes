from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass
class RepoFile:
    path: str
    sha: str
    size: int


class RepoTruthPort:
    def list_files(self, ref=None) -> list[RepoFile]:
        raise NotImplementedError

    def read_file(self, path, ref=None) -> bytes:
        raise NotImplementedError

    def head(self, ref=None) -> str:
        raise NotImplementedError

    def exists(self, path, ref=None) -> bool:
        try:
            self.read_file(path, ref)
            return True
        except Exception:
            return False


class LocalRepoTruth(RepoTruthPort):
    def __init__(self, root):
        self.root = Path(root).resolve()

    def list_files(self, ref=None):
        result = []
        for p in self.root.rglob("*"):
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts:
                data = p.read_bytes()
                result.append(
                    RepoFile(
                        str(p.relative_to(self.root)),
                        hashlib.sha1(data).hexdigest(),
                        len(data),
                    )
                )
        return sorted(result, key=lambda x: x.path)

    def read_file(self, path, ref=None):
        p = (self.root / path).resolve()
        if self.root not in p.parents and p != self.root:
            raise ValueError("path escapes repository")
        return p.read_bytes()

    def head(self, ref=None):
        head = self.root / ".git" / "HEAD"
        return head.read_text(encoding="utf-8").strip() if head.exists() else "LOCAL"
