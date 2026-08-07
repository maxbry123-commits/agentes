"""LocalProvider · adapta doc_registry + session_store (nativo, sin Tencent)."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, List

from memory.doc_registry import DocRegistry
from memory.ondemand import rank_docs
from memory.schemas.context import MemoryContext, MemoryNamespace, MemoryRecord
from memory.session_store import SessionStore


class LocalProvider:
    name = "local"

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.docs = DocRegistry(self.root / "docs.jsonl")
        self.session = SessionStore(self.root / "session.jsonl")

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "provider": self.name,
            "docs": len(self.docs),
            "session_events": len(self.session),
            "tip_docs": self.docs.tip_hash(),
            "tip_session": self.session.tip_hash,
        }

    def capture(
        self,
        ctx: MemoryContext,
        content: str,
        *,
        type: str = "raw",
        meta: dict | None = None,
    ) -> MemoryRecord:
        ns = MemoryNamespace.from_context(ctx)
        self.session.append(
            "capture",
            {
                "ns": ns.value,
                "type": type,
                "project": ctx.project_id,
                "agent": ctx.agent_id,
            },
        )
        if type in ("doc", "semantic", "fact") or (meta or {}).get("register_doc"):
            rec = self.docs.register(
                name=(meta or {}).get("name") or f"mem_{ctx.task_id or 'x'}",
                source=(meta or {}).get("source") or "local",
                content=content,
                summary=(meta or {}).get("summary") or content[:200],
                tags=list((meta or {}).get("tags") or [type, ctx.project_id]),
                meta={"ns": ns.value, **(meta or {})},
            )
            mid = rec.doc_id
            ch = rec.content_hash
        else:
            mid = "loc_" + hashlib.sha256(content.encode()).hexdigest()[:12]
            ch = "sha256:" + hashlib.sha256(content.encode()).hexdigest()
        return MemoryRecord(
            id=mid,
            content=content,
            type=type,
            namespace=ns.value,
            project_id=ctx.project_id,
            agent_id=ctx.agent_id,
            source="local",
            version=ctx.memory_version,
            meta={"content_hash": ch, **(meta or {})},
        )

    def recall(
        self,
        ctx: MemoryContext,
        query: str,
        *,
        top_n: int = 10,
    ) -> List[MemoryRecord]:
        ns = MemoryNamespace.from_context(ctx)
        ranked = rank_docs(self.docs, query, top_n=top_n)
        out: List[MemoryRecord] = []
        for r in ranked:
            # aislamiento blando: filtrar por project en tags/meta si existe
            if ctx.project_id and ctx.project_id not in r.record.tags:
                if r.record.meta.get("ns") and ctx.project_id not in str(r.record.meta.get("ns")):
                    # permitir si no hay señal de otro proyecto
                    other = r.record.meta.get("project_id")
                    if other and other != ctx.project_id:
                        continue
            out.append(
                MemoryRecord(
                    id=r.record.doc_id,
                    content=r.record.summary or r.record.name,
                    type="doc",
                    namespace=ns.value,
                    project_id=ctx.project_id,
                    agent_id=ctx.agent_id,
                    source=r.record.source,
                    importance=min(1.0, r.score / 5.0),
                    meta={"score": r.score, "name": r.record.name},
                )
            )
        return out
