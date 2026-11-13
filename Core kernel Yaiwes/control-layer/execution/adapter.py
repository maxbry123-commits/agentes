"""D01 · ExecutionAdapter · Local primero · Temporal opcional detras."""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class ActivityResult:
    activity_id: str
    status: RunStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class ExecutionAdapter(Protocol):
    name: str

    def start_workflow(self, workflow_id: str, payload: dict[str, Any]) -> str: ...

    def run_activity(
        self,
        workflow_id: str,
        activity: str,
        payload: dict[str, Any],
    ) -> ActivityResult: ...

    def signal(self, workflow_id: str, signal_name: str, data: dict[str, Any] | None = None) -> None: ...

    def health(self) -> dict[str, Any]: ...


class LocalExecutionAdapter:
    """Motor local determinista — núcleo sin Temporal."""

    name = "local"

    def __init__(self) -> None:
        self._workflows: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register_activity(self, name: str, fn: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._handlers[name] = fn

    def start_workflow(self, workflow_id: str, payload: dict[str, Any]) -> str:
        run_id = workflow_id or ("run_" + uuid.uuid4().hex[:10])
        self._workflows[run_id] = {
            "payload": dict(payload),
            "status": RunStatus.RUNNING.value,
            "signals": [],
            "started_at": time.time(),
        }
        return run_id

    def run_activity(
        self,
        workflow_id: str,
        activity: str,
        payload: dict[str, Any],
    ) -> ActivityResult:
        aid = "act_" + uuid.uuid4().hex[:10]
        t0 = time.time()
        if workflow_id not in self._workflows:
            return ActivityResult(aid, RunStatus.FAILED, error="workflow_not_found")
        fn = self._handlers.get(activity)
        if fn is None:
            return ActivityResult(
                aid,
                RunStatus.SUCCESS,
                output={"echo": payload, "activity": activity},
                duration_ms=(time.time() - t0) * 1000,
            )
        try:
            out = fn(dict(payload))
            return ActivityResult(
                aid,
                RunStatus.SUCCESS,
                output=dict(out or {}),
                duration_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:  # noqa: BLE001
            return ActivityResult(
                aid,
                RunStatus.FAILED,
                error=str(e),
                duration_ms=(time.time() - t0) * 1000,
            )

    def signal(self, workflow_id: str, signal_name: str, data: dict[str, Any] | None = None) -> None:
        wf = self._workflows.get(workflow_id)
        if wf is None:
            raise KeyError("workflow_not_found")
        wf["signals"].append({"name": signal_name, "data": dict(data or {}), "ts": time.time()})

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "adapter": self.name,
            "workflows": len(self._workflows),
            "activities": list(self._handlers),
        }


class TemporalExecutionAdapterStub:
    """Stub opcional — no es núcleo. Falla claro si no hay cliente."""

    name = "temporal_stub"

    def start_workflow(self, workflow_id: str, payload: dict[str, Any]) -> str:
        raise RuntimeError("temporal_not_configured")

    def run_activity(
        self,
        workflow_id: str,
        activity: str,
        payload: dict[str, Any],
    ) -> ActivityResult:
        return ActivityResult("act_na", RunStatus.FAILED, error="temporal_not_configured")

    def signal(self, workflow_id: str, signal_name: str, data: dict[str, Any] | None = None) -> None:
        raise RuntimeError("temporal_not_configured")

    def health(self) -> dict[str, Any]:
        return {"status": "unconfigured", "adapter": self.name}
