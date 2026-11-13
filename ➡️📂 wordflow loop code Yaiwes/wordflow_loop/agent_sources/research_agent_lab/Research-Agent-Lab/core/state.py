from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from schemas.base import utc_now
from datetime import datetime
from uuid import uuid4


def _new_run_id() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{uuid4().hex[:6]}"
from schemas.topic_pack import TopicPack


@dataclass(slots=True)
class ResearchState:
    topic: TopicPack
    run_id: str = field(default_factory=_new_run_id)
    stage: str = "initialized"
    created_at: str = field(default_factory=utc_now)
    values: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, list[str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def add_artifact(self, kind: str, artifact_id: str) -> None:
        self.artifacts.setdefault(kind, []).append(artifact_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "stage": self.stage,
            "created_at": self.created_at,
            "topic": self.topic.to_dict(),
            "values": self.values,
            "artifacts": self.artifacts,
            "notes": self.notes,
        }
