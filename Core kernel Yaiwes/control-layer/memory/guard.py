"""MC04 · MemoryGuard · aislamiento proyecto/agente · test cimiento."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from memory.policy import MemoryPolicy, PolicyDecision
from memory.schemas.context import MemoryContext, MemoryNamespace, MemoryRecord


class MemoryAccessDenied(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    decision: PolicyDecision
    namespace: str


class MemoryGuard:
    def __init__(self, policy: MemoryPolicy | None = None) -> None:
        self.policy = policy or MemoryPolicy()

    def check_write(self, ctx: MemoryContext) -> GuardResult:
        d = self.policy.evaluate(ctx)
        ns = MemoryNamespace.from_context(ctx).value
        if not d.allow_write:
            raise MemoryAccessDenied(";".join(d.reasons) or "write_denied")
        return GuardResult(ok=True, decision=d, namespace=ns)

    def check_read(self, ctx: MemoryContext) -> GuardResult:
        d = self.policy.evaluate(ctx)
        ns = MemoryNamespace.from_context(ctx).value
        if not d.allow_read:
            raise MemoryAccessDenied(";".join(d.reasons) or "read_denied")
        return GuardResult(ok=True, decision=d, namespace=ns)

    def record_visible(self, ctx: MemoryContext, rec: MemoryRecord) -> bool:
        """True si el record pertenece al namespace/proyecto del ctx."""
        if rec.project_id and ctx.project_id and rec.project_id != ctx.project_id:
            if ctx.memory_scope != "global":
                return False
        ns = MemoryNamespace.from_context(ctx).value
        if rec.namespace and ctx.memory_scope == "private":
            # private: debe coincidir agent en namespace
            if f"agent/{ctx.agent_id}" not in rec.namespace and rec.agent_id and rec.agent_id != ctx.agent_id:
                return False
        if rec.namespace and ctx.memory_scope == "project":
            if ctx.project_id not in rec.namespace and rec.project_id not in ("", ctx.project_id):
                return False
        return True
