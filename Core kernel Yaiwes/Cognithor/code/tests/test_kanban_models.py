"""Tests for Kanban data models."""

from __future__ import annotations

import json

from cognithor.kanban.models import (
    Task,
    TaskHistory,
    TaskPriority,
    TaskSource,
    TaskStatus,
)


class TestTaskStatus:
    def test_all_values(self):
        assert len(TaskStatus) == 7
        assert TaskStatus.TODO == "todo"
        assert TaskStatus.PENDING_REVIEW == "pending_review"
        assert TaskStatus.CANCELLED == "cancelled"


class TestTaskPriority:
    def test_all_values(self):
        assert len(TaskPriority) == 4
        assert TaskPriority.URGENT == "urgent"


class TestTaskSource:
    def test_all_values(self):
        assert len(TaskSource) == 6
        assert TaskSource.AGENT == "agent"


class TestTask:
    def test_create_minimal(self):
        t = Task(title="Test task")
        assert t.title == "Test task"
        assert t.status == TaskStatus.TODO
        assert t.priority == TaskPriority.MEDIUM
        assert t.source == TaskSource.MANUAL
        assert t.id
        assert t.created_at

    def test_to_dict(self):
        t = Task(title="Test", assigned_agent="coder")
        d = t.to_dict()
        assert d["title"] == "Test"
        assert d["assigned_agent"] == "coder"
        assert "id" in d

    def test_from_dict(self):
        t = Task(title="Original", labels=["bug", "urgent"])
        d = t.to_dict()
        t2 = Task.from_dict(d)
        assert t2.title == "Original"
        assert t2.labels == ["bug", "urgent"]
        assert t2.id == t.id

    def test_labels_json_roundtrip(self):
        t = Task(title="Test", labels=["a", "b"])
        raw = t.labels_json
        assert json.loads(raw) == ["a", "b"]

    def test_sub_task(self):
        parent = Task(title="Parent")
        child = Task(title="Child", parent_id=parent.id)
        assert child.parent_id == parent.id


class TestTaskHistory:
    def test_create(self):
        h = TaskHistory(
            task_id="abc",
            old_status="todo",
            new_status="in_progress",
            changed_by="user",
        )
        assert h.old_status == "todo"
        assert h.changed_at
