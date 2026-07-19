 <estador-universal/orchestrator/state.py 2>/dev/null
"""
state.py — WorkflowState con persistencia atómica y reanudación.

Reglas:
- atomic_write_json con fsync + os.replace (P0-1)
- SHA-256 de goal para Goal Lock (G1)
- SHA-256 de orquestador para replay determinista (G7)
- Thread-safe con lock
"""
import json
import os
import time
import hashlib
import tempfile
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


def atomic_write_json(path: str, data: dict) -> None:
    """P0-1: write-to-temp + fsync + os.replace. SIGKILL-safe."""
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise


def hash_goal(goal: str) -> str:
    """SHA-256 del goal. Usado en Goal Lock (G1)."""
    return hashlib.sha256(goal.encode("utf-8")).hexdigest()[:16]


@dataclass
class WorkflowState:
    input_data: dict
    goal_hash: str = ""
    current_node: Optional[str] = None
    completed_nodes: List[str] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    repair_counts: Dict[str, int] = field(default_factory=dict)
    node_results: Dict[str, dict] = field(default_factory=dict)
    approvals: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    orchestrator_sha: str = ""

    STATE_PATH = "workflow_state.json"
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self):
        # G1: Goal Lock
        objetivo = self.input_data.get("objetivo", "")
        if objetivo and not self.goal_hash:
            self.goal_hash = hash_goal(objetivo)
        # G7: SHA del orquestador para replay determinista
        if not self.orchestrator_sha:
            try:
                from orchestrator.orchestrator import ORCHESTRATOR_VERSION
                self.orchestrator_sha = hashlib.sha256(
                    ORCHESTRATOR_VERSION.encode()).hexdigest()[:16]
            except ImportError:
                self.orchestrator_sha = "unknown"

    def persist(self, path: str = None) -> None:
        path = path or self.STATE_PATH
        with self._lock:
            try:
                atomic_write_json(path, {
                    "input_data": self.input_data,
                    "goal_hash": self.goal_hash,
                    "current_node": self.current_node,
                    "completed_nodes": self.completed_nodes,
                    "retry_counts": self.retry_counts,
                    "repair_counts": self.repair_counts,
                    "node_results": self.node_results,
                    "approvals": self.approvals,
                    "errors": self.errors,
                    "metrics": self.metrics,
                    "start_time": self.start_time,
                    "orchestrator_sha": self.orchestrator_sha,
                    "ts": time.time(),
                })
            except Exception as e:
                self.errors.append(f"persist_failed: {e}")

    @classmethod
    def load(cls, path: str = None, input_data: dict = None) -> "WorkflowState":
        path = path or cls.STATE_PATH
        state = cls(input_data=input_data or {})
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                # G7: validar SHA del orquestador
                stored_sha = data.get("orchestrator_sha", "")
                if stored_sha and stored_sha != state.orchestrator_sha:
                    state.errors.append(
                        f"REPLAY_SHA_MISMATCH: stored={stored_sha} current={state.orchestrator_sha}")
                state.input_data = data.get("input_data", input_data or {})
                state.goal_hash = data.get("goal_hash", "")
                state.current_node = data.get("current_node")
                state.completed_nodes = data.get("completed_nodes", [])
                state.retry_counts = data.get("retry_counts", {})
                state.repair_counts = data.get("repair_counts", {})
                state.node_results = data.get("node_results", {})
                state.approvals = data.get("approvals", {})
                state.errors = data.get("errors", [])
                state.metrics = data.get("metrics", {})
                state.start_time = data.get("start_time", time.time())
            except Exception as e:
                state.errors.append(f"state_load_error: {e}")
        return state

    def add_error(self, msg: str) -> None:
        self.errors.append(f"{time.strftime('%H:%M:%S')} {msg}")
root@vmi3428294:~# echo 