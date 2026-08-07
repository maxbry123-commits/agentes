"""MemoryRouter · decide provider · isolation por MemoryContext."""
from __future__ import annotations

from typing import Any, List, Optional

from memory.providers.base import MemoryProvider
from memory.schemas.context import MemoryContext, MemoryRecord


class MemoryRouter:
    def __init__(self, primary: MemoryProvider, *, secondary: MemoryProvider | None = None) -> None:
        self.primary = primary
        self.secondary = secondary

    def health(self) -> dict[str, Any]:
        h = {"primary": self.primary.health()}
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
    ) -> MemoryRecord:
        if "write" not in ctx.permissions:
            raise PermissionError("memory_write_denied")
        rec = self.primary.capture(ctx, content, type=type, meta=meta)
        if also_secondary and self.secondary is not None:
            try:
                self.secondary.capture(ctx, content, type=type, meta=meta)
            except Exception:
                pass
        return rec

    def recall(self, ctx: MemoryContext, query: str, *, top_n: int = 10) -> List[MemoryRecord]:
        if "read" not in ctx.permissions:
            raise PermissionError("memory_read_denied")
        out = self.primary.recall(ctx, query, top_n=top_n)
        if self.secondary is not None and len(out) < top_n:
            try:
                extra = self.secondary.recall(ctx, query, top_n=top_n - len(out))
                out.extend(extra)
            except Exception:
                pass
        return out[:top_n]
