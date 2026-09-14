from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict

ALLOWED_TASK_TYPES = {
    "research", "code_review", "documentation", "data_transform",
    "unit_test", "integration_test_mock", "report", "checkpoint", "handoff",
}


class PolicyError(ValueError):
    pass


class CheckpointStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, workflow_id: str, link_id: str) -> Path:
        workflow_key = hashlib.sha256(workflow_id.encode()).hexdigest()[:24]
        link_key = hashlib.sha256(link_id.encode()).hexdigest()[:24]
        return self.root / workflow_key / f"{link_key}.json"

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


class SafeTaskAdapter:
    """Local inert adapter; it never invokes C2, MCP, sockets, shell or security tools."""
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("task_type")
        if task_type not in ALLOWED_TASK_TYPES:
            raise PolicyError(f"TASK_TYPE_NOT_ALLOWED:{task_type}")
        payload = json.dumps(task.get("payload", {}), ensure_ascii=False, sort_keys=True, default=str)
        return {
            "task_type": task_type,
            "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "accepted": True,
            "network": "disabled",
            "subprocess": "disabled",
            "c2": "disabled",
            "mcp_offensive_tools": "disabled",
        }


class PersistenceWorkflowLink:
    def __init__(self, store: CheckpointStore, max_retries: int = 3, adapter: SafeTaskAdapter | None = None):
        self.store = store
        self.link_id = "02-CyberStrikeAI"
        self.next_link = "03-LuaN1aoAgent"
        self.max_retries = max_retries
        self.adapter = adapter or SafeTaskAdapter()

    def run(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        for field in ("workflow_id", "task_id", "task"):
            if field not in envelope:
                raise PolicyError(f"MISSING_FIELD:{field}")
        state = self.store.load(envelope["workflow_id"], self.link_id)
        if state and state.get("status") == "HANDOFF_READY":
            return state
        if not state:
            state = {
                "schema": "yaiwes.coda.persistence-link/v1",
                "workflow_id": envelope["workflow_id"],
                "task_id": envelope["task_id"],
                "link_id": self.link_id,
                "next_link": self.next_link,
                "task": envelope["task"],
                "attempts": 0,
                "status": "PENDING",
                "result": None,
                "error": None,
            }

        while state["attempts"] < self.max_retries:
            state["attempts"] += 1
            state["status"] = "RUNNING"
            state["error"] = None
            self.store.save(state["workflow_id"], self.link_id, state)
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
                self.store.save(state["workflow_id"], self.link_id, state)
                return state
            except Exception as exc:
                state["status"] = "RETRY_PENDING"
                state["error"] = f"{type(exc).__name__}:{exc}"
                self.store.save(state["workflow_id"], self.link_id, state)

        state["status"] = "FAILED"
        self.store.save(state["workflow_id"], self.link_id, state)
        return state
