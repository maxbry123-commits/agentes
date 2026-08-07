"""Loop Supervisor — F4 + P1 heartbeat events + JSONL persist · 0% LLM
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loops.contracts.types import LoopContext, LoopCommand, LoopEvent
from loops.dlq import DLQItem, DeadLetterQueue
from loops.engine import LoopEngine, LoopRunResult
from loops.heartbeat import HeartbeatMonitor
from loops.lease import LeaseManager
from loops.persist import JsonlStore
from loops.registry import LoopRegistry
from loops.state_machine import StateMachine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SupervisorConfig:
    max_concurrent: int = 50
    worker_id: str = "worker-local"
    lease_ttl_seg: int = 30
    persist_dir: str | None = None  # if set → JSONL


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
        self._store: JsonlStore | None = None
        if self.config.persist_dir:
            self._store = JsonlStore(Path(self.config.persist_dir) / "supervisor.jsonl")

    def _persist(self, kind: str, payload: dict[str, Any]) -> None:
        if self._store:
            self._store.append({"ts": _now(), "kind": kind, **payload})

    def _heartbeat_event(self, run_id: str) -> LoopEvent:
        import hashlib
        eid = f"hb-{run_id}-{_now()}"
        prev = ""
        h = hashlib.sha256(f"{eid}|{run_id}|HEARTBEAT|{{}}|{prev}".encode()).hexdigest()
        return LoopEvent(
            event_id=eid, run_id=run_id, type="HEARTBEAT",
            timestamp=_now(), prev_hash=prev, hash=h,
            payload={"owner": self.config.worker_id}, actor="supervisor",
        )

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
        ev = self._heartbeat_event(ctx.run_id)
        self.engine._emit(ev)
        self._persist("create", {"run_id": ctx.run_id, "project_id": ctx.project_id, "state": ctx.state})
        return ctx

    def run_once(self, run_id: str, **kwargs: Any) -> LoopRunResult:
        ctx = self._contexts.get(run_id)
        if not ctx:
            raise KeyError(run_id)
        if not self.leases.renew(run_id, self.config.worker_id):
            raise RuntimeError("lease lost")
        self.heartbeat.beat(run_id, self.config.worker_id)
        self.engine._emit(self._heartbeat_event(run_id))
        result = self.engine.run_iteration(ctx, **kwargs)
        self._contexts[run_id] = result.ctx
        self.registry.upsert(result.ctx)
        self._persist("run_once", {
            "run_id": run_id, "state": result.ctx.state,
            "closed": result.closed, "iteration": result.ctx.iteration,
        })
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
                self._persist("dlq", {"run_id": run_id, "state": result.ctx.state})
        return result

    def apply_command(self, cmd: LoopCommand) -> LoopContext:
        ctx = self._contexts.get(cmd.run_id)
        if not ctx:
            raise KeyError(cmd.run_id)
        target = self.sm.apply_command_state(ctx, cmd.command)
        if target is None:
            raise ValueError(f"command {cmd.command} invalid in state {ctx.state}")
        ctx, _ev = self.sm.transition(ctx, target, event_type=f"COMMAND_{cmd.command}", actor=cmd.issued_by)
        self._contexts[cmd.run_id] = ctx
        self.registry.upsert(ctx)
        self._persist("command", {"run_id": cmd.run_id, "command": cmd.command, "state": ctx.state})
        if target in ("CANCELLED", "FAILED"):
            self.leases.release(cmd.run_id, self.config.worker_id)
            self.heartbeat.remove(cmd.run_id)
        return ctx

    def recover_orphans(self) -> list[str]:
        recovered: list[str] = []
        for rid in self.leases.reclaim_expired():
            ctx = self._contexts.get(rid)
            if ctx and ctx.state not in ("CLOSED", "CANCELLED"):
                ctx.state = "FAILED"  # type: ignore[assignment]
                self.registry.upsert(ctx)
                self.dlq.enqueue(DLQItem(
                    run_id=rid, project_id=ctx.project_id, agent_id=ctx.agent_id,
                    task_id=ctx.task_id, state="FAILED", reason="lease_expired_orphan",
                ))
                recovered.append(rid)
                self._persist("orphan", {"run_id": rid})
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
