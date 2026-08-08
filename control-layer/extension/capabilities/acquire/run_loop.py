"""RUN_LOOP · kernel mini-loop · Phase 0.

Executes NOOP nodes only (no network). Terminal exits required:
DONE | BLOCKED | FAILED | BUDGET_EXCEEDED

while RUNNABLE:
  stop_policy? → BUDGET_EXCEEDED
  next unit? none → DONE
  lock → execute → verify → checkpoint → journal → memory
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .checkpoint import CheckpointStore
from .journal import Journal
from .lock import LockError, MissionLock
from .memory_ops import MemoryOpsStore
from .queue import TaskQueue
from .registry import MissionRegistry
from .schema import Checkpoint, TERMINAL_STATUSES
from .stop_policy import BudgetUsage, StopPolicyGuard


@dataclass
class NoopNode:
    id: str
    status: str = "PENDING"  # PENDING|DONE|FAILED|SKIPPED


@dataclass
class LoopResult:
    mission_id: str
    status: str
    nodes_run: int = 0
    reason: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "status": self.status,
            "nodes_run": self.nodes_run,
            "reason": self.reason,
            "detail": self.detail,
        }


class RunLoop:
    """Phase 0: DAG is a simple list of NOOP nodes."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.queue = TaskQueue(self.root)
        self.registry = MissionRegistry(self.root)
        self.locks = MissionLock(self.root)
        self.checkpoints = CheckpointStore(self.root)
        self.journal = Journal(self.root)
        self.memory = MemoryOpsStore(self.root)

    def _load_nodes(self, mission_id: str) -> list[NoopNode]:
        """Phase 0: fixed NOOP plan from checkpoint/nodes_total or default 3."""
        cp = self.checkpoints.load_unchecked(mission_id)
        n = 3
        if cp and cp.nodes_total > 0:
            n = cp.nodes_total
        nodes = [NoopNode(id=f"noop-{i}") for i in range(n)]
        # mark already done from checkpoint
        done = cp.nodes_done if cp else 0
        for i, node in enumerate(nodes):
            if i < done:
                node.status = "DONE"
        return nodes

    def _next_pending(self, nodes: list[NoopNode]) -> NoopNode | None:
        for node in nodes:
            if node.status == "PENDING":
                return node
        return None

    def run(
        self,
        mission_id: str,
        *,
        force_lock: bool = False,
        blocked: bool = False,
        fail_on_node: str | None = None,
        handler: Callable[[NoopNode], None] | None = None,
    ) -> LoopResult:
        rec = self.registry.get(mission_id)
        if rec is None:
            return LoopResult(mission_id, "FAILED", reason="mission_not_found")

        if rec.status in TERMINAL_STATUSES:
            return LoopResult(mission_id, rec.status, reason="already_terminal")

        if blocked:
            self.queue.mark_terminal(mission_id, "BLOCKED", next_action="await_human")
            self.registry.set_status(mission_id, "BLOCKED", next_action="await_human")
            self.journal.append(mission_id, "blocked", ok=False, detail={"reason": "sheriff_or_host"})
            return LoopResult(mission_id, "BLOCKED", reason="blocked")

        try:
            self.locks.acquire(mission_id, force=force_lock)
        except LockError as e:
            return LoopResult(mission_id, "BLOCKED", reason="LOCKED", detail=e.holder)

        nodes_run = 0
        try:
            self.queue.mark_running(mission_id)
            self.registry.set_status(mission_id, "RUNNING", next_action="execute")

            policy = StopPolicyGuard(rec.stop_policy)
            usage = BudgetUsage.from_dict(rec.budget)
            if "started_at" not in (rec.budget or {}):
                usage = BudgetUsage(
                    nodes_used=int(rec.budget.get("nodes_used", 0)),
                    bytes_downloaded=int(rec.budget.get("bytes_downloaded", 0)),
                    retries_used=int(rec.budget.get("retries_used", 0)),
                    api_calls_used=int(rec.budget.get("api_calls_used", 0)),
                )

            if not self.checkpoints.exists(mission_id):
                self.checkpoints.init(mission_id, nodes_total=3)
            if not self.memory.exists(mission_id):
                self.memory.init(mission_id, next_action="execute")

            nodes = self._load_nodes(mission_id)

            while True:
                exceeded, reason = policy.exceeded(usage)
                if exceeded:
                    self._finalize(mission_id, "BUDGET_EXCEEDED", usage, reason or "budget")
                    return LoopResult(mission_id, "BUDGET_EXCEEDED", nodes_run, reason)

                unit = self._next_pending(nodes)
                if unit is None:
                    self._finalize(mission_id, "DONE", usage, "dag_complete")
                    return LoopResult(mission_id, "DONE", nodes_run, reason="dag_complete")

                # execute NOOP (or custom handler)
                try:
                    if fail_on_node and unit.id == fail_on_node:
                        raise RuntimeError(f"forced_fail:{unit.id}")
                    if handler:
                        handler(unit)
                    unit.status = "DONE"
                    ok = True
                    err = None
                except Exception as e:  # noqa: BLE001
                    unit.status = "FAILED"
                    ok = False
                    err = str(e)
                    self.journal.append(
                        mission_id, "execute", ok=False, node_id=unit.id, detail={"error": err}
                    )
                    self.memory.update(mission_id, last_error=err, next_action="failed")
                    self._finalize(mission_id, "FAILED", usage, err)
                    return LoopResult(mission_id, "FAILED", nodes_run + 1, reason=err)

                nodes_run += 1
                usage.nodes_used += 1
                self.registry.bump_budget(mission_id, nodes_used=1)

                # verify (phase 0: status DONE)
                if unit.status != "DONE":
                    self._finalize(mission_id, "FAILED", usage, "verify_failed")
                    return LoopResult(mission_id, "FAILED", nodes_run, reason="verify_failed")

                # checkpoint
                done = sum(1 for n in nodes if n.status == "DONE")
                cp = Checkpoint(
                    mission_id=mission_id,
                    node_id=unit.id,
                    nodes_done=done,
                    nodes_total=len(nodes),
                    status="RUNNABLE",
                )
                self.checkpoints.save(cp)

                self.journal.append(
                    mission_id, "execute", ok=ok, node_id=unit.id, detail={"noop": True}
                )
                self.memory.update(
                    mission_id,
                    next_action="execute",
                    clear_error=True,
                    progress={"nodes_done": done, "nodes_total": len(nodes)},
                )

        finally:
            self.locks.release(mission_id)

    def _finalize(
        self,
        mission_id: str,
        status: str,
        usage: BudgetUsage,
        reason: str,
    ) -> None:
        assert status in TERMINAL_STATUSES
        self.queue.mark_terminal(mission_id, status, next_action="idle")  # type: ignore[arg-type]
        self.registry.set_status(mission_id, status, next_action="idle")  # type: ignore[arg-type]
        cp = self.checkpoints.load_unchecked(mission_id) or Checkpoint(mission_id=mission_id)
        cp.status = status  # type: ignore[assignment]
        self.checkpoints.save(cp)
        self.journal.append(
            mission_id, "terminal", ok=(status == "DONE"), detail={"status": status, "reason": reason, "usage": usage.to_dict()}
        )
        self.memory.update(
            mission_id,
            next_action="idle",
            last_error=None if status == "DONE" else reason,
            progress={"terminal": status},
        )
