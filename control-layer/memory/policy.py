"""MC05 · MemoryPolicy · qué puede leer/escribir cada scope."""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from memory.schemas.context import MemoryContext


@dataclass(frozen=True)
class PolicyDecision:
    allow_read: bool
    allow_write: bool
    reasons: tuple[str, ...]


# scope -> permissions default por rol simple
_DEFAULT = {
    "private": frozenset({"read", "write"}),
    "project": frozenset({"read", "write"}),
    "global": frozenset({"read"}),  # write global requiere flag explícito
}


class MemoryPolicy:
    def __init__(self, *, allow_global_write: bool = False) -> None:
        self.allow_global_write = allow_global_write

    def evaluate(self, ctx: MemoryContext) -> PolicyDecision:
        scope = ctx.memory_scope or "project"
        perms = set(ctx.permissions)
        reasons: list[str] = []

        if scope not in _DEFAULT:
            return PolicyDecision(False, False, ("invalid_scope",))

        allow_read = "read" in perms
        allow_write = "write" in perms

        if scope == "global" and allow_write and not self.allow_global_write:
            allow_write = False
            reasons.append("global_write_denied")

        if not allow_read:
            reasons.append("read_not_in_permissions")
        if not allow_write and "write" in perms and scope != "global":
            pass
        elif not allow_write and "write" not in perms:
            reasons.append("write_not_in_permissions")

        return PolicyDecision(allow_read=allow_read, allow_write=allow_write, reasons=tuple(reasons))
