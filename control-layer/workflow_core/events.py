from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping
from uuid import uuid4

from .enums import EventType


@dataclass(frozen=True)
class WorkflowEvent:
    event_id: str
    workflow_id: str
    sequence: int
    event_type: EventType
    timestamp: datetime
    payload: Mapping[str, object]

    @classmethod
    def create(
        cls,
        workflow_id: str,
        sequence: int,
        event_type: EventType,
        payload: Mapping[str, object],
    ) -> "WorkflowEvent":
        return cls(
            event_id=str(uuid4()),
            workflow_id=workflow_id,
            sequence=sequence,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            payload=dict(payload),
        )
