"""RUN_LOOP · kernel mini-loop.

Modes:
  noop  — Phase 0 tests (default if no DAG)
  dag   — real acquire DAG via worker

Terminal: DONE | BLOCKED | FAILED | BUDGET_EXCEEDED
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .checkpoint import CheckpointStore
from .dag import DAG, DagStore, build_acquire_dag
from .journal import Journal
from .lock import LockError, MissionLock
from .memory_ops import MemoryOpsStore
from .queue import TaskQueue
from .registry import MissionRegistry
from .schema import Checkpoint, TERMINAL_STATUSES
from .stop_policy import BudgetUsage, StopPolicyGuard
from .worker import execute_node


@dataclass
class NoopNode:
    id: str
    status: str = "PENDING"


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
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.queue = TaskQueue(self.root)
        self.registry = MissionRegistry(self.root)
        self.locks = MissionLock(self.root)
        self.checkpoints = CheckpointStore(self.root)
        self.journal = Journal(self.root)
        self.memory = MemoryOpsStore(self.root)
        self.dags = DagStore(self.root)

    def run(
        self,
        mission_id: str,
        *,
        force_lock: bool = False,
        blocked: bool = False,
        fail_on_node: str | None = None,
        handler: Callable[[NoopNode], None] | None = None,
        mode: str | None = None,
        token: str | None = None,
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

        # dependency missions must be DONE
        if rec.depends_on:
            for dep in rec.depends_on:
                drec = self.registry.get(dep)
                if drec is None or drec.status != "DONE":
                    self.queue.update_status(mission_id, "BLOCKED", next_action="wait_deps")
                    self.registry.set_status(mission_id, "BLOCKED", next_action="wait_deps")
                    return LoopResult(mission_id, "BLOCKED", reason=f"dep_not_done:{dep}")

        try:
            self.locks.acquire(mission_id, force=force_lock)
        except LockError as e:
            return LoopResult(mission_id, "BLOCKED", reason="LOCKED", detail=e.holder)

        use_dag = mode == "dag" or (mode is None and bool(rec.repo))
        try:
            if use_dag:
                return self._run_dag(mission_id, rec, token=token, fail_on_node=fail_on_node)
            return self._run_noop(mission_id, rec, fail_on_node=fail_on_node, handler=handler)
        finally:
            self.locks.release(mission_id)

    def _run_dag(self, mission_id: str, rec: Any, *,
                 token: str | None, fail_on_node: str | None) -> LoopResult:
        self.queue.mark_running(mission_id)
        self.registry.set_status(mission_id, "RUNNING", next_action="execute")
        policy = StopPolicyGuard(rec.stop_policy)
        usage = BudgetUsage.from_dict(rec.budget)

        dag = self.dags.load(mission_id)
        if dag is None:
            dag = build_acquire_dag(mission_id, dry_run=rec.dry_run, dep_mission_ids=rec.depends_on)
            self.dags.save(dag)

        state_path = self.root / "missions" / mission_id.replace("/", "_") / "state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state: dict[str, Any] = {}
        if state_path.is_file():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                state = {}

        nodes_run = 0
        while True:
            exceeded, reason = policy.exceeded(usage)
            if exceeded:
                self._finalize(mission_id, "BUDGET_EXCEEDED", usage, reason or "budget")
                return LoopResult(mission_id, "BUDGET_EXCEEDED", nodes_run, reason)

            unit = dag.next()
            if unit is None:
                if dag.has_failed():
                    self._finalize(mission_id, "FAILED", usage, "dag_failed")
                    return LoopResult(mission_id, "FAILED", nodes_run, reason="dag_failed")
                self._finalize(mission_id, "DONE", usage, "dag_complete")
                return LoopResult(mission_id, "DONE", nodes_run, reason="dag_complete")

            if fail_on_node and unit.id == fail_on_node:
                dag.mark(unit.id, "FAILED")
                self.dags.save(dag)
                self._finalize(mission_id, "FAILED", usage, f"forced_fail:{unit.id}")
                return LoopResult(mission_id, "FAILED", nodes_run + 1, reason=f"forced_fail:{unit.id}")

            result = execute_node(
                unit,
                root=self.root,
                mission_id=mission_id,
                repo=rec.repo,
                tag=rec.tag,
                commit=rec.commit,
                token=token or (rec.meta or {}).get("token"),
                dest_root=rec.dest_root,
                dry_run=rec.dry_run,
                state=state,
            )
            nodes_run += 1
            usage.nodes_used += 1
            self.registry.bump_budget(mission_id, nodes_used=1)

            if result.get("ok"):
                dag.mark(unit.id, "DONE")
            else:
                if unit.retries < unit.max_retries:
                    unit.retries += 1
                    usage.retries_used += 1
                    self.registry.bump_budget(mission_id, retries_used=1)
                    self.journal.append(
                        mission_id, "retry", ok=False, node_id=unit.id,
                        detail={"error": result.get("error"), "attempt": unit.retries},
                    )
                    self.dags.save(dag)
                    continue
                dag.mark(unit.id, "FAILED")
                self.dags.save(dag)
                state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
                self.journal.append(
                    mission_id, "execute", ok=False, node_id=unit.id,
                    detail={"error": result.get("error")},
                )
                self._finalize(mission_id, "FAILED", usage, str(result.get("error")))
                return LoopResult(mission_id, "FAILED", nodes_run, reason=str(result.get("error")))

            self.dags.save(dag)
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            done = sum(1 for n in dag.nodes if n.status == "DONE")
            cp = Checkpoint(
                mission_id=mission_id,
                node_id=unit.id,
                nodes_done=done,
                nodes_total=len(dag.nodes),
                status="RUNNABLE",
            )
            self.checkpoints.save(cp)
            self.journal.append(mission_id, "execute", ok=True, node_id=unit.id, detail={"op": unit.op})
            self.memory.update(
                mission_id,
                next_action="execute",
                strategy=state.get("strategy"),
                clear_error=True,
                progress={"nodes_done": done, "nodes_total": len(dag.nodes)},
            )

    def _run_noop(self, mission_id: str, rec: Any, *,
                  fail_on_node: str | None,
                  handler: Callable[[NoopNode], None] | None) -> LoopResult:
        self.queue.mark_running(mission_id)
        self.registry.set_status(mission_id, "RUNNING", next_action="execute")
        policy = StopPolicyGuard(rec.stop_policy)
        usage = BudgetUsage.from_dict(rec.budget)

        if not self.checkpoints.exists(mission_id):
            self.checkpoints.init(mission_id, nodes_total=3)
        if not self.memory.exists(mission_id):
            self.memory.init(mission_id, next_action="execute")

        cp = self.checkpoints.load_unchecked(mission_id)
        n = cp.nodes_total if cp and cp.nodes_total > 0 else 3
        nodes = [NoopNode(id=f"noop-{i}") for i in range(n)]
        done0 = cp.nodes_done if cp else 0
        for i, node in enumerate(nodes):
            if i < done0:
                node.status = "DONE"

        nodes_run = 0
        while True:
            exceeded, reason = policy.exceeded(usage)
            if exceeded:
                self._finalize(mission_id, "BUDGET_EXCEEDED", usage, reason or "budget")
                return LoopResult(mission_id, "BUDGET_EXCEEDED", nodes_run, reason)

            unit = next((x for x in nodes if x.status == "PENDING"), None)
            if unit is None:
                self._finalize(mission_id, "DONE", usage, "dag_complete")
                return LoopResult(mission_id, "DONE", nodes_run, reason="dag_complete")

            try:
                if fail_on_node and unit.id == fail_on_node:
                    raise RuntimeError(f"forced_fail:{unit.id}")
                if handler:
                    handler(unit)
                unit.status = "DONE"
            except Exception as e:  # noqa: BLE001
                self.journal.append(mission_id, "execute", ok=False, node_id=unit.id, detail={"error": str(e)})
                self._finalize(mission_id, "FAILED", usage, str(e))
                return LoopResult(mission_id, "FAILED", nodes_run + 1, reason=str(e))

            nodes_run += 1
            usage.nodes_used += 1
            self.registry.bump_budget(mission_id, nodes_used=1)
            done = sum(1 for x in nodes if x.status == "DONE")
            self.checkpoints.save(Checkpoint(
                mission_id=mission_id, node_id=unit.id,
                nodes_done=done, nodes_total=len(nodes), status="RUNNABLE",
            ))
            self.journal.append(mission_id, "execute", ok=True, node_id=unit.id, detail={"noop": True})
            self.memory.update(mission_id, next_action="execute", clear_error=True,
                               progress={"nodes_done": done, "nodes_total": len(nodes)})

    def _finalize(self, mission_id: str, status: str, usage: BudgetUsage, reason: str) -> None:
        assert status in TERMINAL_STATUSES
        self.queue.mark_terminal(mission_id, status, next_action="idle")  # type: ignore[arg-type]
        self.registry.set_status(mission_id, status, next_action="idle")  # type: ignore[arg-type]
        cp = self.checkpoints.load_unchecked(mission_id) or Checkpoint(mission_id=mission_id)
        cp.status = status  # type: ignore[assignment]
        self.checkpoints.save(cp)
        self.journal.append(
            mission_id, "terminal", ok=(status == "DONE"),
            detail={"status": status, "reason": reason, "usage": usage.to_dict()},
        )
        self.memory.update(
            mission_id, next_action="idle",
            last_error=None if status == "DONE" else reason,
            progress={"terminal": status},
        )
