"""W10 · Source Mirror · descarga determinista + hash + no from-scratch."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class SourceEntry:
    source_id: str
    repo_url: str
    ref: str  # tag|branch|commit
    commit_sha: str
    license: str = ""
    category: str = "general"  # frontend|backend|memory|sandbox|agents
    local_path: str = ""
    content_hash: str = ""
    registered_at: float = field(default_factory=time.time)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceMirror:
    """Registro de fuentes OS aprobadas. Nunca editar el source clonado."""

    def __init__(self, index_path: Path) -> None:
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self._by_id: Dict[str, SourceEntry] = {}
        if self.index_path.is_file():
            for line in self.index_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    d = json.loads(line)
                    e = SourceEntry(**{k: d[k] for k in SourceEntry.__dataclass_fields__ if k in d})
                    self._by_id[e.source_id] = e

    def register(
        self,
        *,
        source_id: str,
        repo_url: str,
        ref: str,
        commit_sha: str,
        license: str = "",
        category: str = "general",
        local_path: str = "",
        meta: dict | None = None,
    ) -> SourceEntry:
        if not commit_sha or len(commit_sha) < 7:
            raise ValueError("commit_sha_required")
        content_hash = hashlib.sha256(f"{repo_url}|{ref}|{commit_sha}".encode()).hexdigest()
        e = SourceEntry(
            source_id=source_id,
            repo_url=repo_url,
            ref=ref,
            commit_sha=commit_sha,
            license=license,
            category=category,
            local_path=local_path,
            content_hash="sha256:" + content_hash,
            meta=dict(meta or {}),
        )
        self._by_id[source_id] = e
        with self.index_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        return e

    def get(self, source_id: str) -> SourceEntry | None:
        return self._by_id.get(source_id)

    def by_category(self, category: str) -> list[SourceEntry]:
        return [e for e in self._by_id.values() if e.category == category]

    def require_source(self, source_id: str) -> SourceEntry:
        e = self.get(source_id)
        if e is None:
            raise FileNotFoundError(f"source_not_mirrored:{source_id}")
        return e
