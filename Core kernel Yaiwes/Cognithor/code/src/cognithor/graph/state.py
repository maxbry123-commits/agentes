"""State Manager -- Checkpoint persistence for Graph Orchestrator v18.

Manages:
  - Checkpoint creation and serialization
  - State restore for pause/resume
  - Checkpoint history per execution
  - Disk persistence in ~/.cognithor/graph/checkpoints/
  - Automatic cleanup of old checkpoints

Enables:
  - HITL pause: pause graph, save state, resume later
  - Error recovery: continue from last checkpoint after crash
  - Audit trail: complete state history traceable
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from cognithor.graph.types import (
    Checkpoint,
    ExecutionRecord,
    ExecutionStatus,
    GraphState,
    NodeResult,
)
from cognithor.utils.logging import get_logger

log = get_logger(__name__)


class StateManager:
    """Manages checkpoints and state persistence."""

    def __init__(self, storage_dir: str | Path = "") -> None:
        if storage_dir:
            self._storage_dir = Path(storage_dir)
        else:
            self._storage_dir = Path.home() / ".cognithor" / "graph" / "checkpoints"
        self._checkpoints: dict[str, Checkpoint] = {}
        self._executions: dict[str, ExecutionRecord] = {}

    def _ensure_dir(self) -> None:
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    # ── Checkpoint CRUD ──────────────────────────────────────────

    def create_checkpoint(
        self,
        execution_id: str,
        graph_name: str,
        current_node: str,
        state: GraphState,
        history: list[NodeResult] | None = None,
        status: ExecutionStatus = ExecutionStatus.PAUSED,
    ) -> Checkpoint:
        """Creates a new checkpoint."""
        cp = Checkpoint(
            execution_id=execution_id,
            graph_name=graph_name,
            current_node=current_node,
            state=state.to_dict(),
            history=[r.to_dict() for r in (history or [])],
            status=status,
        )
        self._checkpoints[cp.checkpoint_id] = cp

        # Add to execution
        if execution_id in self._executions:
            self._executions[execution_id].checkpoints.append(cp.checkpoint_id)

        log.debug(
            "checkpoint_created",
            checkpoint_id=cp.checkpoint_id,
            execution_id=execution_id,
            node=current_node,
        )
        return cp

    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Loads checkpoint from cache or disk."""
        if checkpoint_id in self._checkpoints:
            return self._checkpoints[checkpoint_id]
        return self._load_from_disk(checkpoint_id)

    def get_latest_checkpoint(self, execution_id: str) -> Checkpoint | None:
        """Returns the latest checkpoint of an execution."""
        candidates = [cp for cp in self._checkpoints.values() if cp.execution_id == execution_id]
        if not candidates:
            # Also load from disk
            self._load_execution_checkpoints(execution_id)
            candidates = [
                cp for cp in self._checkpoints.values() if cp.execution_id == execution_id
            ]
        if not candidates:
            return None
        return max(candidates, key=lambda c: (c.created_at, c._seq))

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        self._checkpoints.pop(checkpoint_id, None)
        path = self._checkpoint_path(checkpoint_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_checkpoints(self, execution_id: str = "") -> list[Checkpoint]:
        """Lists checkpoints, optionally filtered by execution."""
        if execution_id:
            return [cp for cp in self._checkpoints.values() if cp.execution_id == execution_id]
        return list(self._checkpoints.values())

    # ── State Restore ────────────────────────────────────────────

    def restore_state(self, checkpoint_id: str) -> tuple[GraphState | None, str]:
        """Restores state from checkpoint.

        Returns:
            (GraphState, current_node) or (None, "")
        """
        cp = self.get_checkpoint(checkpoint_id)
        if cp is None:
            return None, ""

        state = GraphState.from_dict(cp.state)
        return state, cp.current_node

    def restore_from_latest(self, execution_id: str) -> tuple[GraphState | None, str]:
        """Restores state from the latest checkpoint."""
        cp = self.get_latest_checkpoint(execution_id)
        if cp is None:
            return None, ""
        return self.restore_state(cp.checkpoint_id)

    # ── Execution Records ────────────────────────────────────────

    def create_execution(self, graph_name: str, initial_state: GraphState) -> ExecutionRecord:
        """Creates a new execution record."""
        record = ExecutionRecord(
            graph_name=graph_name,
            status=ExecutionStatus.RUNNING,
            initial_state=initial_state.to_dict(),
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self._executions[record.execution_id] = record
        return record

    def get_execution(self, execution_id: str) -> ExecutionRecord | None:
        return self._executions.get(execution_id)

    def update_execution(self, record: ExecutionRecord) -> None:
        self._executions[record.execution_id] = record

    def list_executions(
        self, *, status: ExecutionStatus | None = None, limit: int = 50
    ) -> list[ExecutionRecord]:
        records = list(self._executions.values())
        if status:
            records = [r for r in records if r.status == status]
        records.sort(key=lambda r: r.started_at, reverse=True)
        return records[:limit]

    # ── Persistence ──────────────────────────────────────────────

    def save_checkpoint_to_disk(self, checkpoint_id: str) -> bool:
        """Saves checkpoint to disk."""
        cp = self._checkpoints.get(checkpoint_id)
        if cp is None:
            return False
        try:
            import os

            self._ensure_dir()
            path = self._checkpoint_path(checkpoint_id)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(cp.to_json(), encoding="utf-8")
            os.replace(str(tmp), str(path))  # Atomic on both POSIX and Windows
            return True
        except Exception as exc:
            log.warning("checkpoint_save_error", id=checkpoint_id, error=str(exc))
            return False

    def save_all_checkpoints(self) -> int:
        """Saves all checkpoints to disk."""
        saved = 0
        for cp_id in self._checkpoints:
            if self.save_checkpoint_to_disk(cp_id):
                saved += 1
        return saved

    def _checkpoint_path(self, checkpoint_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in checkpoint_id)
        return self._storage_dir / f"{safe}.json"

    def _load_from_disk(self, checkpoint_id: str) -> Checkpoint | None:
        path = self._checkpoint_path(checkpoint_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cp = Checkpoint.from_dict(data)
            self._checkpoints[cp.checkpoint_id] = cp
            return cp
        except Exception as exc:
            log.warning("checkpoint_load_error", id=checkpoint_id, error=str(exc))
            return None

    def _load_execution_checkpoints(self, execution_id: str) -> None:
        """Loads all checkpoints of an execution from disk."""
        if not self._storage_dir.exists():
            return
        for path in self._storage_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("execution_id") == execution_id:
                    cp = Checkpoint.from_dict(data)
                    self._checkpoints[cp.checkpoint_id] = cp
            except Exception as exc:
                log.debug("checkpoint_load_error", path=str(path), error=str(exc))

    # ── Cleanup ──────────────────────────────────────────────────

    def cleanup(self, max_age_days: int = 7, max_checkpoints: int = 1000) -> int:
        """Cleans up old checkpoints."""
        cutoff = time.time() - (max_age_days * 86400)
        removed = 0

        for cp_id in list(self._checkpoints):
            cp = self._checkpoints[cp_id]
            try:
                import calendar

                ts = calendar.timegm(time.strptime(cp.created_at, "%Y-%m-%dT%H:%M:%SZ"))
                if ts < cutoff:
                    self.delete_checkpoint(cp_id)
                    removed += 1
            except (ValueError, OverflowError):
                pass

        # Max limit
        if len(self._checkpoints) > max_checkpoints:
            sorted_cps = sorted(self._checkpoints.values(), key=lambda c: c.created_at)
            for cp in sorted_cps[: len(self._checkpoints) - max_checkpoints]:
                self.delete_checkpoint(cp.checkpoint_id)
                removed += 1

        return removed

    # ── Stats ────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        return {
            "checkpoints": len(self._checkpoints),
            "executions": len(self._executions),
            "active_executions": sum(
                1
                for r in self._executions.values()
                if r.status in (ExecutionStatus.RUNNING, ExecutionStatus.PAUSED)
            ),
            "storage_dir": str(self._storage_dir),
        }
