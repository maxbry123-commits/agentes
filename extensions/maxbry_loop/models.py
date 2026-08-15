from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import uuid


def now():
    return datetime.now(timezone.utc).isoformat()


def uid(prefix="TASK"):
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: str = "pending"
    priority: int = 50
    depends_on: List[str] = field(default_factory=list)
    acceptance: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    attempts: int = 0
    result: Optional[str] = None


@dataclass
class Goal:
    text: str
    source: str = "chat"
    requirements: List[str] = field(default_factory=list)


@dataclass
class Event:
    type: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=now)
    iteration: int = 0


@dataclass
class State:
    schema_version: str
    goal: Goal
    tasks: Dict[str, Task]
    iteration: int = 0
    workflow_version: int = 1
    completion_score: float = 0.0
    blockers: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

    def to_dict(self):
        return {
            "schema_version": self.schema_version,
            "goal": asdict(self.goal),
            "tasks": {k: asdict(v) for k, v in self.tasks.items()},
            "iteration": self.iteration,
            "workflow_version": self.workflow_version,
            "completion_score": self.completion_score,
            "blockers": self.blockers,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }
