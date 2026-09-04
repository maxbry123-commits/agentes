"""MemoryRouter · Guard + Policy + Classifier + Version + Cache."""
from __future__ import annotations

from typing import Any, List

from memory.cache_stub import SimpleCache
from memory.classifier import MemoryClass, classify_memory
from memory.guard import MemoryGuard
from memory.policy import MemoryPolicy
from memory.providers.base import MemoryProvider
from memory.schemas.context import MemoryContext, MemoryRecord
from memory.versioning import CacheKey, VersionManager


class MemoryRouter:
    def __init__(
        self,
        primary: MemoryProvider,
        *,
        secondary: MemoryProvider | None = None,
        guard: MemoryGuard | None = None,
        versions: VersionManager | None = None,
        cache: SimpleCache | None = None,
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.guard = guard or MemoryGuard(MemoryPolicy())
        self.versions = versions
        self.cache = cache or SimpleCache()

    def _ctx(self, ctx: MemoryContext) -> MemoryContext:
        if self.versions is not None:
            return self.versions.attach(ctx)
        return ctx

    def health(self) -> dict[str, Any]:
        h: dict[str, Any] = {"primary": self.primary.health()}
        if self.secondary is not None:
            h["secondary"] = self.secondary.health()
        return h

    def capture(
        self,
        ctx: MemoryContext,
        content: str,
        *,
        type: str = "raw",
        meta: dict | None = None,
        also_secondary: bool = False,
        skip_classifier: bool = False,
    ) -> MemoryRecord | None:
        ctx = self._ctx(ctx)
        self.guard.check_write(ctx)

        if not skip_classifier:
            cm = classify_memory(content, explicit=(meta or {}).get("class"))
            if not cm.store:
                return None
            if type == "raw":
                type = {
                    MemoryClass.TEMPORARY: "raw",
                    MemoryClass.FACT: "fact",
                    MemoryClass.EXPERIENCE: "episodic",
                    MemoryClass.KNOWLEDGE: "semantic",
                    MemoryClass.PROCEDURE: "procedure",
                    MemoryClass.DISCARD: "raw",
                }.get(cm.klass, type)

        rec = self.primary.capture(ctx, content, type=type, meta=meta)
        if self.versions is not None and type in ("fact", "semantic", "procedure", "doc"):
            self.versions.bump(ctx.project_id)
        if also_secondary and self.secondary is not None:
            try:
                self.secondary.capture(ctx, content, type=type, meta=meta)
            except Exception:
                pass
        return rec

    def recall(self, ctx: MemoryContext, query: str, *, top_n: int = 10) -> List[MemoryRecord]:
        ctx = self._ctx(ctx)
        self.guard.check_read(ctx)

        key = CacheKey.build(ctx, kind="recall", query=query)
        cached = self.cache.get(key, current_version=ctx.memory_version)
        if cached is not None:
            return list(cached)[:top_n]

        out = self.primary.recall(ctx, query, top_n=top_n)
        out = [r for r in out if self.guard.record_visible(ctx, r)]
        if self.secondary is not None and len(out) < top_n:
            try:
                extra = self.secondary.recall(ctx, query, top_n=top_n - len(out))
                out.extend(x for x in extra if self.guard.record_visible(ctx, x))
            except Exception:
                pass
        out = out[:top_n]
        self.cache.set(key, out, memory_version=ctx.memory_version)
        return out
