from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

ALLOWED_TASK_TYPES = {
    "research",
    "code_review",
    "documentation",
    "data_transform",
    "unit_test",
    "integration_test_mock",
    "report",
    "checkpoint",
    "handoff",
}

TERMINAL = {"PASSED", "FAILED", "HANDOFF_READY"}


class PolicyError(ValueError):
    pass


class CheckpointStore:
    """Atomic JSON checkpoint store with deterministic per-workflow paths."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, workflow_id: str, link_id: str) -> Path:
        safe_workflow = hashlib.sha256(workflow_id.encode()).hexdigest()[:24]
        safe_link = hashlib.sha256(link_id.encode()).hexdigest()[:24]
        return self.root / safe_workflow / f"{safe_link}.json"

    def save(self, workflow_id: str, link_id: str, state: Dict[str, Any]) -> Path:
        path = self._path(workflow_id, link_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, path)
        return path

    def load(self, workflow_id: str, link_id: str) -> Dict[str, Any] | None:
        path = self._path(workflow_id, link_id)
        return json.loads(path.read_text()) if path.exists() else None


@dataclass
class SafeTaskAdapter:
    """Inert task adapter: no subprocess, shell, sockets, scanners or exploit tools."""

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("task_type")
        if task_type not in ALLOWED_TASK_TYPES:
            raise PolicyError(f"TASK_TYPE_NOT_ALLOWED:{task_type}")
        payload = task.get("payload", {})
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        return {
            "task_type": task_type,
            "payload_sha256": hashlib.sha256(serialized.encode()).hexdigest(),
            "accepted": True,
            "side_effects": "none",
        }


class PersistenceWorkflowLink:
    """DeepAudit-derived benign workflow link with checkpoint/resume/handoff semantics."""

    def __init__(
        self,
        store: CheckpointStore,
        link_id: str = "01-DeepAudit",
        next_link: str = "02-CyberStrikeAI",
        max_retries: int = 3,
        adapter: SafeTaskAdapter | None = None,
    ):
        self.store = store
        self.link_id = link_id
        self.next_link = next_link
        self.max_retries = max_retries
        self.adapter = adapter or SafeTaskAdapter()

    def _new_state(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "schema": "yaiwes.coda.persistence-link/v1",
            "workflow_id": envelope["workflow_id"],
            "task_id": envelope["task_id"],
            "link_id": self.link_id,
            "next_link": self.next_link,
            "status": "PENDING",
            "attempts": 0,
            "task": envelope["task"],
            "result": None,
            "error": None,
        }

    def run(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        for key in ("workflow_id", "task_id", "task"):
            if key not in envelope:
                raise PolicyError(f"MISSING_FIELD:{key}")
        state = self.store.load(envelope["workflow_id"], self.link_id) or self._new_state(envelope)
        if state.get("status") in {"PASSED", "HANDOFF_READY"}:
            return state

        while state["attempts"] < self.max_retries:
            state["attempts"] += 1
            state["status"] = "RUNNING"
            state["error"] = None
            self.store.save(envelope["workflow_id"], self.link_id, state)
            try:
                state["result"] = self.adapter.execute(state["task"])
                state["status"] = "HANDOFF_READY"
                state["handoff"] = {
                    "workflow_id": state["workflow_id"],
                    "task_id": state["task_id"],
                    "from_link": self.link_id,
                    "to_link": self.next_link,
                    "result": state["result"],
                }
                self.store.save(envelope["workflow_id"], self.link_id, state)
                return state
            except Exception as exc:
                state["error"] = f"{type(exc).__name__}:{exc}"
                state["status"] = "RETRY_PENDING"
                self.store.save(envelope["workflow_id"], self.link_id, state)

        state["status"] = "FAILED"
        self.store.save(envelope["workflow_id"], self.link_id, state)
        return state
