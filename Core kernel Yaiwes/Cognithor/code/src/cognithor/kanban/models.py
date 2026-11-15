"""Kanban Board data models."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    VERIFYING = "verifying"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskSource(str, Enum):
    MANUAL = "manual"
    CHAT = "chat"
    CRON = "cron"
    EVOLUTION = "evolution"
    AGENT = "agent"
    SYSTEM = "system"


VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {
        TaskStatus.PENDING_REVIEW,
        TaskStatus.VERIFYING,
        TaskStatus.BLOCKED,
        TaskStatus.CANCELLED,
        TaskStatus.TODO,
    },
    TaskStatus.PENDING_REVIEW: {
        TaskStatus.DONE,  # approved → execute & done
        TaskStatus.IN_PROGRESS,  # rejected → back to work
        TaskStatus.TODO,  # rejected → rethink
        TaskStatus.CANCELLED,
    },
    TaskStatus.VERIFYING: {TaskStatus.DONE, TaskStatus.IN_PROGRESS},
    TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.TODO, TaskStatus.CANCELLED},
    TaskStatus.DONE: set(),
    TaskStatus.CANCELLED: {TaskStatus.TODO},
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Task:
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_agent: str = ""
    source: TaskSource = TaskSource.MANUAL
    source_ref: str = ""
    parent_id: str = ""
    labels: list[str] = field(default_factory=list)
    sort_order: int = 0
    created_by: str = "user"
    result_summary: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    completed_at: str = ""

    @property
    def labels_json(self) -> str:
        return json.dumps(self.labels)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "priority": self.priority.value
            if isinstance(self.priority, TaskPriority)
            else self.priority,
            "assigned_agent": self.assigned_agent,
            "source": self.source.value if isinstance(self.source, TaskSource) else self.source,
            "source_ref": self.source_ref,
            "parent_id": self.parent_id,
            "labels": self.labels,
            "sort_order": self.sort_order,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "created_by": self.created_by,
            "result_summary": self.result_summary,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Task:
        labels = d.get("labels", [])
        if isinstance(labels, str):
            labels = json.loads(labels) if labels else []
        return cls(
            id=d.get("id", uuid.uuid4().hex),
            title=d["title"],
            description=d.get("description", ""),
            status=TaskStatus(d.get("status", "todo")),
            priority=TaskPriority(d.get("priority", "medium")),
            assigned_agent=d.get("assigned_agent", ""),
            source=TaskSource(d.get("source", "manual")),
            source_ref=d.get("source_ref", ""),
            parent_id=d.get("parent_id", ""),
            labels=labels,
            sort_order=d.get("sort_order", 0),
            created_at=d.get("created_at", _now_iso()),
            updated_at=d.get("updated_at", _now_iso()),
            completed_at=d.get("completed_at", ""),
            created_by=d.get("created_by", "user"),
            result_summary=d.get("result_summary", ""),
        )


@dataclass
class TaskHistory:
    task_id: str
    old_status: str
    new_status: str
    changed_by: str
    note: str = ""
    id: int = 0
    changed_at: str = field(default_factory=_now_iso)
