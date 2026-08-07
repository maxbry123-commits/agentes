"""W05 · Input Gateway · cola 1..N sin bloquear misión."""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, List

from input.classifier import ClassifiedInput, InputKind, classify_hot_input


@dataclass
class QueuedInput:
    input_id: str
    text: str
    kind: InputKind
    mission_id: str | None
    created_at: float
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


class InputGateway:
    def __init__(self, capacity: int = 50) -> None:
        self.capacity = capacity
        self._queue: List[QueuedInput] = []

    def receive(
        self,
        text: str,
        *,
        mission_id: str | None = None,
        meta: dict | None = None,
    ) -> QueuedInput:
        if len(self._queue) >= self.capacity:
            raise RuntimeError("input_queue_full")
        c: ClassifiedInput = classify_hot_input(text)
        # NEW_TASK never binds to current mission
        mid = None if c.kind == InputKind.NEW_TASK else mission_id
        item = QueuedInput(
            input_id="in_" + uuid.uuid4().hex[:12],
            text=text,
            kind=c.kind,
            mission_id=mid,
            created_at=time.time(),
            meta={**(meta or {}), "classify": c.to_dict()},
        )
        self._queue.append(item)
        return item

    def pending(self, mission_id: str | None = None) -> list[QueuedInput]:
        if mission_id is None:
            return list(self._queue)
        return [q for q in self._queue if q.mission_id == mission_id or q.kind == InputKind.NEW_TASK]

    def pop_next(self, mission_id: str | None = None) -> QueuedInput | None:
        for i, q in enumerate(self._queue):
            if mission_id is None or q.mission_id == mission_id or q.kind == InputKind.NEW_TASK:
                return self._queue.pop(i)
        return None

    def __len__(self) -> int:
        return len(self._queue)
