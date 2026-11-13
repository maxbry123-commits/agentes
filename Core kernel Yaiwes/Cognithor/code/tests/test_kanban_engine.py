"""Tests for KanbanEngine business logic."""

from __future__ import annotations

import pytest

from cognithor.kanban.engine import (
    InvalidTransition,
    KanbanEngine,
    SubtaskDepthExceeded,
    TaskLimitExceeded,
)
from cognithor.kanban.models import TaskSource, TaskStatus
from cognithor.kanban.store import KanbanStore


@pytest.fixture
def engine(tmp_path):
    store = KanbanStore(str(tmp_path / "kanban.db"), use_encryption=False)
    return KanbanEngine(
        store,
        max_auto_tasks=5,
        max_subtask_depth=2,
        cascade_cancel=True,
    )


class TestCreateTask:
    def test_create_manual(self, engine):
        t = engine.create_task("Test", source=TaskSource.MANUAL, created_by="user")
        assert t.title == "Test"
        assert t.status == TaskStatus.TODO

    def test_create_with_agent(self, engine):
        t = engine.create_task("Test", assigned_agent="coder", created_by="user")
        assert t.assigned_agent == "coder"

    def test_auto_task_limit(self, engine):
        for i in range(5):
            engine.create_task(f"Auto {i}", source=TaskSource.AGENT, created_by="agent")
        with pytest.raises(TaskLimitExceeded):
            engine.create_task("Too many", source=TaskSource.AGENT, created_by="agent")

    def test_manual_ignores_limit(self, engine):
        for i in range(10):
            engine.create_task(f"Manual {i}", source=TaskSource.MANUAL, created_by="user")

    def test_subtask_depth_limit(self, engine):
        t1 = engine.create_task("Level 0", created_by="user")
        t2 = engine.create_task("Level 1", parent_id=t1.id, created_by="user")
        t3 = engine.create_task("Level 2", parent_id=t2.id, created_by="user")
        with pytest.raises(SubtaskDepthExceeded):
            engine.create_task("Level 3", parent_id=t3.id, created_by="user")


class TestTransitions:
    def test_valid_transition(self, engine):
        t = engine.create_task("Test", created_by="user")
        updated = engine.transition(t.id, TaskStatus.IN_PROGRESS, changed_by="user")
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_invalid_transition(self, engine):
        t = engine.create_task("Test", created_by="user")
        with pytest.raises(InvalidTransition):
            engine.transition(t.id, TaskStatus.DONE, changed_by="user")

    def test_done_is_terminal(self, engine):
        t = engine.create_task("Test", created_by="user")
        engine.transition(t.id, TaskStatus.IN_PROGRESS, changed_by="user")
        engine.transition(t.id, TaskStatus.VERIFYING, changed_by="user")
        engine.transition(t.id, TaskStatus.DONE, changed_by="user")
        with pytest.raises(InvalidTransition):
            engine.transition(t.id, TaskStatus.TODO, changed_by="user")

    def test_cancelled_can_reopen(self, engine):
        t = engine.create_task("Test", created_by="user")
        engine.transition(t.id, TaskStatus.CANCELLED, changed_by="user")
        reopened = engine.transition(t.id, TaskStatus.TODO, changed_by="user")
        assert reopened.status == TaskStatus.TODO

    def test_transition_records_history(self, engine):
        t = engine.create_task("Test", created_by="user")
        engine.transition(t.id, TaskStatus.IN_PROGRESS, changed_by="user")
        history = engine.get_history(t.id)
        assert len(history) == 1
        assert history[0].old_status == "todo"
        assert history[0].new_status == "in_progress"

    def test_done_sets_completed_at(self, engine):
        t = engine.create_task("Test", created_by="user")
        engine.transition(t.id, TaskStatus.IN_PROGRESS, changed_by="user")
        engine.transition(t.id, TaskStatus.VERIFYING, changed_by="user")
        done = engine.transition(t.id, TaskStatus.DONE, changed_by="user")
        assert done.completed_at != ""


class TestSubtaskLifecycle:
    def test_cancel_cascades(self, engine):
        parent = engine.create_task("Parent", created_by="user")
        child1 = engine.create_task("Child1", parent_id=parent.id, created_by="user")
        child2 = engine.create_task("Child2", parent_id=parent.id, created_by="user")
        engine.transition(parent.id, TaskStatus.CANCELLED, changed_by="user")
        assert engine.get_task(child1.id).status == TaskStatus.CANCELLED
        assert engine.get_task(child2.id).status == TaskStatus.CANCELLED

    def test_all_subtasks_done_parent_verifying(self, engine):
        parent = engine.create_task("Parent", created_by="user")
        engine.transition(parent.id, TaskStatus.IN_PROGRESS, changed_by="user")
        child = engine.create_task("Child", parent_id=parent.id, created_by="user")
        engine.transition(child.id, TaskStatus.IN_PROGRESS, changed_by="user")
        engine.transition(child.id, TaskStatus.VERIFYING, changed_by="user")
        engine.transition(child.id, TaskStatus.DONE, changed_by="user")
        parent_now = engine.get_task(parent.id)
        assert parent_now.status == TaskStatus.VERIFYING

    def test_delete_cascades(self, engine):
        parent = engine.create_task("Parent", created_by="user")
        child = engine.create_task("Child", parent_id=parent.id, created_by="user")
        engine.delete_task(parent.id)
        assert engine.get_task(child.id) is None


class TestResetAutoCounter:
    def test_reset(self, engine):
        for i in range(5):
            engine.create_task(f"Auto {i}", source=TaskSource.AGENT, created_by="agent")
        engine.reset_auto_counter()
        engine.create_task("After reset", source=TaskSource.AGENT, created_by="agent")
