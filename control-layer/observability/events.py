"""W12 · Event Store append-only · trazabilidad determinista."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

GENESIS = "sha256:" + ("0" * 64)


@dataclass
class Event:
    event_id: str
    workflow_id: str
    task_id: str = ""
    node_id: str = ""
    actor: str = "system"
    event_type: str = "info"
    state: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    prev_hash: str = GENESIS
    chain_hash: str = ""
    timestamp: float = field(default_factory=time.time)

    def compute_hash(self) -> str:
        payload = {
            "event_id": self.event_id,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "node_id": self.node_id,
            "actor": self.actor,
            "event_type": self.event_type,
            "state": self.state,
            "evidence": self.evidence,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
        return "sha256:" + hashlib.sha256(raw).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._tip = GENESIS
        self._count = 0
        if self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    d = json.loads(line)
                    self._tip = d.get("chain_hash") or self._tip
                    self._count += 1

    @property
    def tip_hash(self) -> str:
        return self._tip

    def __len__(self) -> int:
        return self._count

    def append(
        self,
        *,
        workflow_id: str,
        event_type: str,
        actor: str = "system",
        task_id: str = "",
        node_id: str = "",
        state: str = "",
        evidence: dict | None = None,
    ) -> Event:
        ev = Event(
            event_id="ev_" + uuid.uuid4().hex[:12],
            workflow_id=workflow_id,
            task_id=task_id,
            node_id=node_id,
            actor=actor,
            event_type=event_type,
            state=state,
            evidence=dict(evidence or {}),
            prev_hash=self._tip,
        )
        ev.chain_hash = ev.compute_hash()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev.to_dict(), ensure_ascii=False) + "\n")
        self._tip = ev.chain_hash
        self._count += 1
        return ev

    def by_workflow(self, workflow_id: str) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("workflow_id") == workflow_id:
                out.append(d)
        return out
