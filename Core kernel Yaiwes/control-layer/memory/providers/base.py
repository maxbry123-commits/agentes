"""MemoryProvider · interfaz única · Local | Tencent | futuro."""
from __future__ import annotations

from typing import Any, List, Protocol

from memory.schemas.context import MemoryContext, MemoryRecord


class MemoryProvider(Protocol):
    name: str

    def health(self) -> dict[str, Any]: ...

    def capture(self, ctx: MemoryContext, content: str, *, type: str = "raw", meta: dict | None = None) -> MemoryRecord: ...

    def recall(self, ctx: MemoryContext, query: str, *, top_n: int = 10) -> List[MemoryRecord]: ...
