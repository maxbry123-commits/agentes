"""Loop Supervisor — crea/pausa/cancela/prioriza/recupera · 0% LLM
SOURCE: Fase 4 · orquesta muchos LoopEngine runs
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from loops.contracts.types import LoopContext, LoopCommand
from loops.dlq import DLQItem, DeadLetterQueue
from loops.engine import LoopEngine, LoopRunResult
from loops.heartbeat import HeartbeatMonitor
from loops.lease import LeaseManager
from loops.registry import LoopRegistry
from loops.state_machine import StateMachine


@dataclass
class SupervisorConfig:
    max_concurrent: int = 50
    worker_id: str = "worker-local"
    lease_ttl_seg: int = 30


class LoopSupervisor:
    def __init__(
        self,
        engine: LoopEngine | None = None,
        config: SupervisorConfig | None = None,
    ):
        self.engine = engine or LoopEngine.with_default_policy()
        self.config = config or SupervisorConfig()
        self.registry = LoopRegistry()
        self.leases = LeaseManager(default_ttl_seg=self.config.lease_ttl_seg)
        self.heartbeat = HeartbeatMonitor()
        self.dlq = DeadLetterQueue()
        self.sm = StateMachine()
        self._contexts: dict[str, LoopContext] = {}

    def create(self, ctx: LoopContext) -> LoopContext:
        active = len(self.registry.find_active())
        if active >= self.config.max_concurrent:
            raise RuntimeError(f"max_concurrent={self.config.max_concurrent} reached")
        lease = self.leases.acquire(ctx.run_id, self.config.worker_id)
        if lease is None:
            raise RuntimeError(f"lease held for {ctx.run_id}")
        self._contexts[ctx.run_id] = ctx
        self.registry.upsert(ctx)
        self.heartbeat.beat(ctx.run_id, self.config.worker_id)
        return ctx

    def run_once(self, run_id: str, **kwargs: Any) -> LoopRunResult:
        ctx = self._contexts.get(run_id)
        if not ctx:
            raise KeyError(run_id)
        if not self.leases.renew(run_id, self.config.worker_id):
            raise RuntimeError("lease lost")
        self.heartbeat.beat(run_id, self.config.worker_id)
        result = self.engine.run_iteration(ctx, **kwargs)
        self._contexts[run_id] = result.ctx
        self.registry.upsert(result.ctx)
        if result.closed:
            self.leases.release(run_id, self.config.worker_id)
            self.heartbeat.remove(run_id)
            if result.ctx.state in ("FAILED", "ESCALATED"):
                self.dlq.enqueue(DLQItem(
                    run_id=run_id,
                    project_id=result.ctx.project_id,
                    agent_id=result.ctx.agent_id,
                    task_id=result.ctx.task_id,
                    state=result.ctx.state,
                    reason=(result.last_decision.reason if result.last_decision else "closed_failed"),
                    errors=list(result.ctx.errors or []),
                    repair_count=int((result.ctx.recovery_state or {}).get("repair_count") or 0),
                ))
        return result

    def apply_command(self, cmd: LoopCommand) -> LoopContext:
        ctx = self._contexts.get(cmd.run_id)
        if not ctx:
            raise KeyError(cmd.run_id)
        target = self.sm.apply_command_state(ctx, cmd.command)
        if target is None:
            raise ValueError(f"command {cmd.command} invalid in state {ctx.state}")
        etype = f"COMMAND_{cmd.command}"
        ctx, _ev = self.sm.transition(ctx, target, event_type=etype, actor=cmd.issued_by)
        self._contexts[cmd.run_id] = ctx
        self.registry.upsert(ctx)
        if target in ("CANCELLED", "FAILED"):
            self.leases.release(cmd.run_id, self.config.worker_id)
            self.heartbeat.remove(cmd.run_id)
        return ctx

    def recover_orphans(self) -> list[str]:
        """Lease expired o DEAD heartbeat → marcar y DLQ."""
        recovered: list[str] = []
        for rid in self.leases.reclaim_expired():
            ctx = self._contexts.get(rid)
            if ctx and ctx.state not in ("CLOSED", "CANCELLED"):
                ctx.state = "FAILED"  # type: ignore[assignment]
                self.registry.upsert(ctx)
                self.dlq.enqueue(DLQItem(
                    run_id=rid,
                    project_id=ctx.project_id,
                    agent_id=ctx.agent_id,
                    task_id=ctx.task_id,
                    state="FAILED",
                    reason="lease_expired_orphan",
                ))
                recovered.append(rid)
        for rid, health in self.heartbeat.stalled_or_dead().items():
            if health == "DEAD" and rid not in recovered:
                recovered.append(rid)
        return recovered

    def requeue_from_dlq(self, run_id: str) -> LoopContext | None:
        item = self.dlq.requeue(run_id)
        if not item:
            return None
        ctx = self._contexts.get(run_id)
        if not ctx:
            return None
        ctx.state = "LOCKED"  # type: ignore[assignment]
        ctx.recovery_state = {**(ctx.recovery_state or {}), "from_dlq": True, "requeue": item.requeue_count}
        self.create(ctx)
        return ctx
