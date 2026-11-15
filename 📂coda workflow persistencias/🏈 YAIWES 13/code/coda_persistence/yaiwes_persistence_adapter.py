from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_STATUS = {"PENDING", "CLAIMED", "RUNNING", "CHECKPOINTED", "VERIFIED", "FAILED", "RELEASED"}

@dataclass
class TaskState:
    task_id: str
    status: str = "PENDING"
    attempts: int = 0
    checkpoint: Dict[str, Any] | None = None
    evidence: List[Dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if self.checkpoint is None:
            self.checkpoint = {}
        if self.evidence is None:
            self.evidence = []

class YaiwesPersistenceAdapter:
    """Safe persistence link. Never executes vendor/source code."""
    def __init__(self, state_path: str | Path) -> None:
        self.state_path = Path(state_path)

    def load(self, task_id: str) -> TaskState:
        if not self.state_path.exists():
            return TaskState(task_id=task_id)
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        if data.get("task_id") != task_id:
            return TaskState(task_id=task_id)
        return TaskState(**data)

    def save(self, state: TaskState) -> None:
        if state.status not in ALLOWED_STATUS:
            raise ValueError(f"invalid status: {state.status}")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)

    def claim(self, task_id: str) -> TaskState:
        state = self.load(task_id)
        if state.status not in {"PENDING", "FAILED", "RELEASED"}:
            raise RuntimeError(f"task not claimable: {state.status}")
        state.status = "CLAIMED"
        state.attempts += 1
        self.save(state)
        return state

    def checkpoint_task(self, task_id: str, payload: Dict[str, Any]) -> TaskState:
        state = self.load(task_id)
        if state.status not in {"CLAIMED", "RUNNING", "CHECKPOINTED"}:
            raise RuntimeError(f"task not checkpointable: {state.status}")
        state.status = "CHECKPOINTED"
        state.checkpoint = dict(payload)
        self.save(state)
        return state

    def verify(self, task_id: str, evidence: Dict[str, Any]) -> TaskState:
        state = self.load(task_id)
        state.status = "VERIFIED"
        state.evidence.append(dict(evidence))
        self.save(state)
        return state

    def release(self, task_id: str) -> TaskState:
        state = self.load(task_id)
        state.status = "RELEASED"
        self.save(state)
        return state
