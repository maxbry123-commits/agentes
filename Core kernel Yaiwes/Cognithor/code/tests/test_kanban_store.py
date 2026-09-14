"""Tests for KanbanStore (SQLite persistence)."""

from __future__ import annotations

import pytest

from cognithor.kanban.models import Task, TaskPriority, TaskStatus
from cognithor.kanban.store import KanbanStore


@pytest.fixture
def store(tmp_path):
    db_path = str(tmp_path / "kanban_test.db")
    s = KanbanStore(db_path, use_encryption=False)
    return s


class TestKanbanStoreCRUD:
    def test_create_and_get(self, store):
        t = Task(title="Test task", assigned_agent="coder")
        store.create(t)
        loaded = store.get(t.id)
        assert loaded is not None
        assert loaded.title == "Test task"
        assert loaded.assigned_agent == "coder"

    def test_get_nonexistent(self, store):
        assert store.get("nonexistent") is None

    def test_list_all(self, store):
        store.create(Task(title="A"))
        store.create(Task(title="B"))
        tasks = store.list_tasks()
        assert len(tasks) == 2

    def test_list_filter_status(self, store):
        store.create(Task(title="A", status=TaskStatus.TODO))
        store.create(Task(title="B", status=TaskStatus.DONE))
        todo = store.list_tasks(status=TaskStatus.TODO)
        assert len(todo) == 1
        assert todo[0].title == "A"

    def test_list_filter_agent(self, store):
        store.create(Task(title="A", assigned_agent="coder"))
        store.create(Task(title="B", assigned_agent="researcher"))
        coder_tasks = store.list_tasks(agent="coder")
        assert len(coder_tasks) == 1

    def test_list_filter_priority(self, store):
        store.create(Task(title="A", priority=TaskPriority.URGENT))
        store.create(Task(title="B", priority=TaskPriority.LOW))
        urgent = store.list_tasks(priority=TaskPriority.URGENT)
        assert len(urgent) == 1

    def test_list_filter_parent(self, store):
        parent = Task(title="Parent")
        child = Task(title="Child", parent_id=parent.id)
        store.create(parent)
        store.create(child)
        children = store.list_tasks(parent_id=parent.id)
        assert len(children) == 1
        assert children[0].title == "Child"

    def test_update(self, store):
        t = Task(title="Original")
        store.create(t)
        store.update(t.id, status="in_progress", assigned_agent="researcher")
        loaded = store.get(t.id)
        assert loaded.status == TaskStatus.IN_PROGRESS
        assert loaded.assigned_agent == "researcher"

    def test_delete(self, store):
        t = Task(title="Delete me")
        store.create(t)
        store.delete(t.id)
        assert store.get(t.id) is None

    def test_delete_cascading(self, store):
        parent = Task(title="Parent")
        child1 = Task(title="Child1", parent_id=parent.id)
        child2 = Task(title="Child2", parent_id=parent.id)
        store.create(parent)
        store.create(child1)
        store.create(child2)
        store.delete(parent.id, cascade=True)
        assert store.get(parent.id) is None
        assert store.get(child1.id) is None
        assert store.get(child2.id) is None

    def test_move(self, store):
        t = Task(title="Move me")
        store.create(t)
        store.move(t.id, new_status="in_progress", sort_order=5)
        loaded = store.get(t.id)
        assert loaded.status == TaskStatus.IN_PROGRESS
        assert loaded.sort_order == 5

    def test_get_subtasks(self, store):
        parent = Task(title="Parent")
        child = Task(title="Child", parent_id=parent.id)
        store.create(parent)
        store.create(child)
        subs = store.get_subtasks(parent.id)
        assert len(subs) == 1

    def test_count_by_status(self, store):
        store.create(Task(title="A", status=TaskStatus.TODO))
        store.create(Task(title="B", status=TaskStatus.TODO))
        store.create(Task(title="C", status=TaskStatus.DONE))
        stats = store.stats()
        assert stats["by_status"]["todo"] == 2
        assert stats["by_status"]["done"] == 1
        assert stats["total"] == 3


class TestKanbanStoreHistory:
    def test_record_history(self, store):
        t = Task(title="Test")
        store.create(t)
        store.record_history(t.id, "todo", "in_progress", "user")
        history = store.get_history(t.id)
        assert len(history) == 1
        assert history[0].old_status == "todo"
        assert history[0].new_status == "in_progress"

    def test_history_ordered(self, store):
        t = Task(title="Test")
        store.create(t)
        store.record_history(t.id, "todo", "in_progress", "user")
        store.record_history(t.id, "in_progress", "done", "user")
        history = store.get_history(t.id)
        assert len(history) == 2
        assert history[0].new_status == "in_progress"
        assert history[1].new_status == "done"
