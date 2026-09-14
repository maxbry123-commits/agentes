from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_TASK_TYPES = {
    "research", "code_review", "documentation", "data_transform",
    "unit_test", "integration_test_mock", "report", "checkpoint", "handoff",
}


class PolicyError(ValueError):
    pass


class EventCheckpointStore:
    """Atomic snapshot + append-style event list inside the state document."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, workflow_id: str, link_id: str) -> Path:
        wk = hashlib.sha256(workflow_id.encode()).hexdigest()[:24]
        lk = hashlib.sha256(link_id.encode()).hexdigest()[:24]
        return self.root / wk / f"{lk}.json"

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

    @staticmethod
    def event(state: Dict[str, Any], event_type: str, **details: Any) -> None:
        events: List[Dict[str, Any]] = state.setdefault("events", [])
        events.append({"seq": len(events) + 1, "type": event_type, "details": details})


class SafeTaskAdapter:
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("task_type")
        if task_type not in ALLOWED_TASK_TYPES:
            raise PolicyError(f"TASK_TYPE_NOT_ALLOWED:{task_type}")
        payload = json.dumps(task.get("payload", {}), ensure_ascii=False, sort_keys=True, default=str)
        return {
            "task_type": task_type,
            "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "accepted": True,
            "scanners": "disabled",
            "bruteforce": "disabled",
            "post_exploit": "disabled",
            "side_effects": "none",
        }


class PersistenceWorkflowLink:
    def __init__(self, store: EventCheckpointStore, max_retries: int = 3, adapter: SafeTaskAdapter | None = None):
        self.store = store
        self.link_id = "04-AI-Pentest"
        self.next_link = "05-AI-Infra-Guard"
        self.max_retries = max_retries
        self.adapter = adapter or SafeTaskAdapter()

    def run(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        for field in ("workflow_id", "task_id", "task"):
            if field not in envelope:
                raise PolicyError(f"MISSING_FIELD:{field}")

        state = self.store.load(envelope["workflow_id"], self.link_id)
        if state and state.get("status") == "HANDOFF_READY":
            return state
        if state is None:
            state = {
                "schema": "yaiwes.coda.persistence-link/v1",
                "workflow_id": envelope["workflow_id"],
                "task_id": envelope["task_id"],
                "link_id": self.link_id,
                "next_link": self.next_link,
                "task": envelope["task"],
                "attempts": 0,
                "status": "PENDING",
                "events": [],
                "result": None,
                "error": None,
            }
            self.store.event(state, "session_created")
            self.store.save(state["workflow_id"], self.link_id, state)

        while state["attempts"] < self.max_retries:
            state["attempts"] += 1
            state["status"] = "RUNNING"
            state["error"] = None
            self.store.event(state, "attempt_started", attempt=state["attempts"])
            self.store.save(state["workflow_id"], self.link_id, state)
            try:
                state["result"] = self.adapter.execute(state["task"])
                self.store.event(state, "task_verified", task_type=state["task"].get("task_type"))
                state["status"] = "HANDOFF_READY"
                state["handoff"] = {
                    "workflow_id": state["workflow_id"],
                    "task_id": state["task_id"],
                    "from_link": self.link_id,
                    "to_link": self.next_link,
                    "result": state["result"],
                }
                self.store.event(state, "handoff_ready", to_link=self.next_link)
                self.store.save(state["workflow_id"], self.link_id, state)
                return state
            except Exception as exc:
                state["status"] = "RETRY_PENDING"
                state["error"] = f"{type(exc).__name__}:{exc}"
                self.store.event(state, "attempt_failed", attempt=state["attempts"], error=state["error"])
                self.store.save(state["workflow_id"], self.link_id, state)

        state["status"] = "FAILED"
        self.store.event(state, "failed_closed", attempts=state["attempts"])
        self.store.save(state["workflow_id"], self.link_id, state)
        return state
