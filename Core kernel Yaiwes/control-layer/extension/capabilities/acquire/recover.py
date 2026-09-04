"""RECOVER · rehydrate missions after interrupt · Phase 0.

TASK_QUEUE → RUNNING/RUNNABLE → CHECKPOINT → stale lock? → RUNNABLE
Does not restart from zero.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .checkpoint import CheckpointStore
from .journal import Journal
from .lock import MissionLock
from .memory_ops import MemoryOpsStore
from .queue import TaskQueue
from .registry import MissionRegistry
from .schema import TERMINAL_STATUSES


@dataclass
class RecoverResult:
    mission_id: str
    action: str  # restored|already_terminal|not_found|cleared_stale_lock
    status: str
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "action": self.action,
            "status": self.status,
            "detail": self.detail,
        }


class RecoverService:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.queue = TaskQueue(self.root)
        self.registry = MissionRegistry(self.root)
        self.locks = MissionLock(self.root, stale_after_sec=60.0)
        self.checkpoints = CheckpointStore(self.root)
        self.journal = Journal(self.root)
        self.memory = MemoryOpsStore(self.root)

    def recover(self, mission_id: str, *,
                force_clear_lock: bool = False) -> RecoverResult:
        rec = self.registry.get(mission_id)
        qe = self.queue.get(mission_id)
        if rec is None and qe is None:
            return RecoverResult(mission_id, "not_found", "FAILED")

        status = (rec.status if rec else qe.status)  # type: ignore[union-attr]
        if status in TERMINAL_STATUSES:
            return RecoverResult(mission_id, "already_terminal", status)

        # clear stale or forced lock
        cleared = False
        if self.locks.is_locked(mission_id):
            if force_clear_lock:
                self.locks.release(mission_id)
                cleared = True
            else:
                try:
                    self.locks.acquire(mission_id, force=False)
                    self.locks.release(mission_id)
                except Exception:
                    # try stale path
                    self.locks.acquire(mission_id, force=True)
                    self.locks.release(mission_id)
                    cleared = True

        # ensure checkpoint + memory exist
        cp = self.checkpoints.load_unchecked(mission_id)
        if cp is None:
            self.checkpoints.init(mission_id, nodes_total=3)
            cp = self.checkpoints.load_unchecked(mission_id)

        if not self.memory.exists(mission_id):
            done = cp.nodes_done if cp else 0
            total = cp.nodes_total if cp else 3
            self.memory.init(mission_id, next_action="execute")
            self.memory.update(
                mission_id,
                progress={"nodes_done": done, "nodes_total": total},
            )

        # RUNNING / interrupted → RUNNABLE
        if status in ("RUNNING", "QUEUED", "RUNNABLE"):
            self.queue.update_status(mission_id, "RUNNABLE", next_action="execute")
            if rec is not None:
                self.registry.set_status(mission_id, "RUNNABLE", next_action="execute")
            self.journal.append(
                mission_id,
                "recover",
                ok=True,
                detail={
                    "from_status": status,
                    "cleared_lock": cleared or force_clear_lock,
                    "nodes_done": cp.nodes_done if cp else 0,
                },
            )
            self.memory.update(mission_id, next_action="execute", clear_error=True)
            return RecoverResult(
                mission_id,
                "cleared_stale_lock" if cleared else "restored",
                "RUNNABLE",
                detail={"previous": status},
            )

        return RecoverResult(mission_id, "restored", status)

    def recover_all(self) -> list[RecoverResult]:
        """Recover every non-terminal mission in the queue."""
        results: list[RecoverResult] = []
        for e in self.queue.list_all():
            if e.status in TERMINAL_STATUSES:
                continue
            results.append(self.recover(e.mission_id))
        return results
