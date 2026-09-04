"""MC06 · memory_version por proyecto + CacheKey."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from memory.schemas.context import MemoryContext


@dataclass(frozen=True)
class CacheKey:
    value: str

    @staticmethod
    def build(
        ctx: MemoryContext,
        *,
        kind: str,
        query: str = "",
        policy_version: int = 1,
    ) -> "CacheKey":
        raw = "|".join(
            [
                ctx.tenant_id,
                ctx.project_id,
                ctx.agent_id,
                ctx.memory_scope,
                str(ctx.memory_version),
                str(policy_version),
                kind,
                hashlib.sha256(query.encode()).hexdigest()[:16],
            ]
        )
        return CacheKey(value=raw)


class VersionManager:
    """Persistencia simple project_id -> version."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._versions: Dict[str, int] = {}
        if self.path.is_file():
            self._versions = json.loads(self.path.read_text(encoding="utf-8") or "{}")

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._versions, indent=2), encoding="utf-8")

    def get(self, project_id: str) -> int:
        return int(self._versions.get(project_id, 0))

    def bump(self, project_id: str) -> int:
        v = self.get(project_id) + 1
        self._versions[project_id] = v
        self._save()
        return v

    def attach(self, ctx: MemoryContext) -> MemoryContext:
        v = self.get(ctx.project_id)
        return MemoryContext(
            tenant_id=ctx.tenant_id,
            project_id=ctx.project_id,
            agent_id=ctx.agent_id,
            workflow_id=ctx.workflow_id,
            task_id=ctx.task_id,
            session_id=ctx.session_id,
            memory_scope=ctx.memory_scope,
            memory_version=v,
            permissions=ctx.permissions,
        )
