# Kanban Board — Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Kanban backend: data models, encrypted SQLite store, business logic engine with guards, source adapters, REST API, MCP tools, and WebSocket broadcasting.

**Architecture:** New `src/jarvis/kanban/` package with 6 files. KanbanStore handles encrypted SQLite persistence. KanbanEngine enforces business rules (status transitions, sub-task lifecycle, creation guards). Source adapters detect task-creation intents from chat, cron, evolution, and system events. FastAPI router exposes 10 REST endpoints. 3 MCP tools let agents manage tasks.

**Tech Stack:** Python 3.12+, SQLite/SQLCipher (via `encrypted_connect()`), FastAPI, Pydantic, pytest

---

### Task 1: KanbanConfig in config.py

**Files:**
- Modify: `src/jarvis/config.py:2224` (after ArcConfig)

- [ ] **Step 1: Add KanbanConfig class**

Add after the `ArcConfig` class definition (around line 2060) and before `JarvisConfig`:

```python
class KanbanConfig(BaseModel):
    """Kanban Board configuration."""

    enabled: bool = True
    max_auto_tasks_per_session: int = Field(default=10, ge=1, le=50)
    max_subtask_depth: int = Field(default=3, ge=1, le=5)
    ws_debounce_ms: int = Field(default=500, ge=100, le=2000)
    auto_create_from_chat: bool = True
    auto_create_from_cron: bool = True
    auto_create_from_evolution: bool = True
    auto_create_from_agents: bool = True
    auto_verify_on_complete: bool = False
    cascade_cancel_subtasks: bool = True
    default_priority: str = "medium"
    default_agent: str = "jarvis"
    archive_after_days: int = Field(default=30, ge=7, le=365)
    columns: list[str] = Field(
        default_factory=lambda: ["todo", "in_progress", "verifying", "done", "blocked"]
    )
    custom_labels: list[str] = Field(default_factory=list)
```

- [ ] **Step 2: Add kanban field to JarvisConfig**

In the `JarvisConfig` class, after the `arc` field (line 2224), add:

```python
    kanban: KanbanConfig = Field(default_factory=KanbanConfig)
```

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/config.py
git commit -m "feat(kanban): add KanbanConfig to JarvisConfig"
```

---

### Task 2: Kanban Models

**Files:**
- Create: `src/jarvis/kanban/__init__.py`
- Create: `src/jarvis/kanban/models.py`
- Test: `tests/test_kanban_models.py`

- [ ] **Step 1: Create package init**

```python
"""Cognithor Kanban Board — interactive task management."""
```

- [ ] **Step 2: Write tests for models**

```python
"""Tests for Kanban data models."""

from __future__ import annotations

import json

import pytest

from jarvis.kanban.models import (
    Task,
    TaskHistory,
    TaskPriority,
    TaskSource,
    TaskStatus,
)


class TestTaskStatus:
    def test_all_values(self):
        assert len(TaskStatus) == 6
        assert TaskStatus.TODO == "todo"
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
        assert t.id  # UUID auto-generated
        assert t.created_at  # timestamp auto-generated

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
        assert h.changed_at  # auto-generated
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_kanban_models.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 4: Implement models.py**

```python
"""Kanban Board data models."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
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


# Valid status transitions
VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {
        TaskStatus.VERIFYING,
        TaskStatus.BLOCKED,
        TaskStatus.CANCELLED,
        TaskStatus.TODO,
    },
    TaskStatus.VERIFYING: {TaskStatus.DONE, TaskStatus.IN_PROGRESS},
    TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.TODO, TaskStatus.CANCELLED},
    TaskStatus.DONE: set(),  # terminal
    TaskStatus.CANCELLED: {TaskStatus.TODO},  # reopen
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
            "priority": self.priority.value if isinstance(self.priority, TaskPriority) else self.priority,
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
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_kanban_models.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/kanban/__init__.py src/jarvis/kanban/models.py tests/test_kanban_models.py
git commit -m "feat(kanban): data models — Task, TaskHistory, enums, transitions"
```

---

### Task 3: KanbanStore (SQLite CRUD)

**Files:**
- Create: `src/jarvis/kanban/store.py`
- Test: `tests/test_kanban_store.py`

- [ ] **Step 1: Write store tests**

```python
"""Tests for KanbanStore (SQLite persistence)."""

from __future__ import annotations

import pytest

from jarvis.kanban.models import Task, TaskPriority, TaskSource, TaskStatus
from jarvis.kanban.store import KanbanStore


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_kanban_store.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement store.py**

```python
"""KanbanStore — encrypted SQLite persistence for Kanban tasks."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from jarvis.kanban.models import (
    Task,
    TaskHistory,
    TaskPriority,
    TaskSource,
    TaskStatus,
    _now_iso,
)
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT NOT NULL DEFAULT 'medium',
    assigned_agent TEXT DEFAULT '',
    source TEXT NOT NULL DEFAULT 'manual',
    source_ref TEXT DEFAULT '',
    parent_id TEXT DEFAULT '',
    labels TEXT DEFAULT '[]',
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT DEFAULT '',
    created_by TEXT NOT NULL DEFAULT 'user',
    result_summary TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT,
    changed_by TEXT,
    changed_at TEXT NOT NULL,
    note TEXT DEFAULT '',
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(assigned_agent);
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id);
CREATE INDEX IF NOT EXISTS idx_history_task ON task_history(task_id);
"""


class KanbanStore:
    """SQLite-backed store for Kanban tasks with optional SQLCipher encryption."""

    def __init__(self, db_path: str, use_encryption: bool = True) -> None:
        self._db_path = db_path
        self._use_encryption = use_encryption
        self._conn: sqlite3.Connection | None = None
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        if self._use_encryption:
            try:
                from jarvis.security.encrypted_db import encrypted_connect
                self._conn = encrypted_connect(self._db_path)
            except Exception:
                self._conn = sqlite3.connect(self._db_path)
        else:
            self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def _ensure_schema(self) -> None:
        conn = self._get_conn()
        conn.executescript(_SCHEMA)
        conn.commit()

    def create(self, task: Task) -> Task:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO tasks (id, title, description, status, priority,
               assigned_agent, source, source_ref, parent_id, labels,
               sort_order, created_at, updated_at, completed_at,
               created_by, result_summary)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                task.id, task.title, task.description,
                task.status.value if isinstance(task.status, TaskStatus) else task.status,
                task.priority.value if isinstance(task.priority, TaskPriority) else task.priority,
                task.assigned_agent,
                task.source.value if isinstance(task.source, TaskSource) else task.source,
                task.source_ref, task.parent_id,
                task.labels_json, task.sort_order,
                task.created_at, task.updated_at, task.completed_at,
                task.created_by, task.result_summary,
            ),
        )
        conn.commit()
        return task

    def get(self, task_id: str) -> Task | None:
        row = self._get_conn().execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_task(row)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        agent: str | None = None,
        priority: TaskPriority | None = None,
        source: TaskSource | None = None,
        parent_id: str | None = None,
        label: str | None = None,
    ) -> list[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[Any] = []

        if status is not None:
            query += " AND status = ?"
            params.append(status.value if isinstance(status, TaskStatus) else status)
        if agent is not None:
            query += " AND assigned_agent = ?"
            params.append(agent)
        if priority is not None:
            query += " AND priority = ?"
            params.append(priority.value if isinstance(priority, TaskPriority) else priority)
        if source is not None:
            query += " AND source = ?"
            params.append(source.value if isinstance(source, TaskSource) else source)
        if parent_id is not None:
            query += " AND parent_id = ?"
            params.append(parent_id)
        if label is not None:
            query += " AND labels LIKE ?"
            params.append(f'%"{label}"%')

        query += " ORDER BY sort_order ASC, created_at DESC"
        rows = self._get_conn().execute(query, params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def update(self, task_id: str, **fields: Any) -> Task | None:
        if not fields:
            return self.get(task_id)
        fields["updated_at"] = _now_iso()
        if "labels" in fields and isinstance(fields["labels"], list):
            fields["labels"] = json.dumps(fields["labels"])
        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [task_id]
        self._get_conn().execute(
            f"UPDATE tasks SET {sets} WHERE id = ?", vals
        )
        self._get_conn().commit()
        return self.get(task_id)

    def delete(self, task_id: str, cascade: bool = True) -> None:
        conn = self._get_conn()
        if cascade:
            conn.execute("DELETE FROM tasks WHERE parent_id = ?", (task_id,))
        conn.execute("DELETE FROM task_history WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

    def move(self, task_id: str, new_status: str, sort_order: int = 0) -> Task | None:
        now = _now_iso()
        completed = now if new_status == TaskStatus.DONE.value else ""
        self._get_conn().execute(
            "UPDATE tasks SET status=?, sort_order=?, updated_at=?, completed_at=? WHERE id=?",
            (new_status, sort_order, now, completed, task_id),
        )
        self._get_conn().commit()
        return self.get(task_id)

    def get_subtasks(self, parent_id: str) -> list[Task]:
        return self.list_tasks(parent_id=parent_id)

    def record_history(
        self, task_id: str, old_status: str, new_status: str,
        changed_by: str, note: str = "",
    ) -> None:
        self._get_conn().execute(
            """INSERT INTO task_history (task_id, old_status, new_status,
               changed_by, changed_at, note) VALUES (?,?,?,?,?,?)""",
            (task_id, old_status, new_status, changed_by, _now_iso(), note),
        )
        self._get_conn().commit()

    def get_history(self, task_id: str) -> list[TaskHistory]:
        rows = self._get_conn().execute(
            "SELECT * FROM task_history WHERE task_id = ? ORDER BY id ASC",
            (task_id,),
        ).fetchall()
        return [
            TaskHistory(
                id=r["id"], task_id=r["task_id"],
                old_status=r["old_status"], new_status=r["new_status"],
                changed_by=r["changed_by"], changed_at=r["changed_at"],
                note=r["note"] or "",
            )
            for r in rows
        ]

    def stats(self) -> dict[str, Any]:
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        by_status: dict[str, int] = {}
        for row in conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ):
            by_status[row["status"]] = row["cnt"]
        by_agent: dict[str, int] = {}
        for row in conn.execute(
            "SELECT assigned_agent, COUNT(*) as cnt FROM tasks "
            "WHERE assigned_agent != '' GROUP BY assigned_agent"
        ):
            by_agent[row["assigned_agent"]] = row["cnt"]
        by_source: dict[str, int] = {}
        for row in conn.execute(
            "SELECT source, COUNT(*) as cnt FROM tasks GROUP BY source"
        ):
            by_source[row["source"]] = row["cnt"]
        return {
            "total": total,
            "by_status": by_status,
            "by_agent": by_agent,
            "by_source": by_source,
        }

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        labels = row["labels"]
        if isinstance(labels, str):
            try:
                labels = json.loads(labels)
            except (json.JSONDecodeError, TypeError):
                labels = []
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            status=TaskStatus(row["status"]),
            priority=TaskPriority(row["priority"]),
            assigned_agent=row["assigned_agent"] or "",
            source=TaskSource(row["source"]),
            source_ref=row["source_ref"] or "",
            parent_id=row["parent_id"] or "",
            labels=labels,
            sort_order=row["sort_order"] or 0,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"] or "",
            created_by=row["created_by"] or "user",
            result_summary=row["result_summary"] or "",
        )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_kanban_store.py -v`
Expected: ALL PASS (17 tests)

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/kanban/store.py tests/test_kanban_store.py
git commit -m "feat(kanban): KanbanStore — encrypted SQLite CRUD with history"
```

---

### Task 4: KanbanEngine (Business Logic)

**Files:**
- Create: `src/jarvis/kanban/engine.py`
- Test: `tests/test_kanban_engine.py`

- [ ] **Step 1: Write engine tests**

```python
"""Tests for KanbanEngine business logic."""

from __future__ import annotations

import pytest

from jarvis.kanban.engine import InvalidTransition, KanbanEngine, SubtaskDepthExceeded, TaskLimitExceeded
from jarvis.kanban.models import Task, TaskPriority, TaskSource, TaskStatus
from jarvis.kanban.store import KanbanStore


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
        # No exception — manual tasks bypass the auto-limit

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
            engine.transition(t.id, TaskStatus.DONE, changed_by="user")  # TODO → DONE not allowed

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
        # Parent should auto-move to VERIFYING
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
        # Should be able to create again
        engine.create_task("After reset", source=TaskSource.AGENT, created_by="agent")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_kanban_engine.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement engine.py**

```python
"""KanbanEngine — business logic for task management."""

from __future__ import annotations

from typing import Any

from jarvis.kanban.models import (
    Task,
    TaskHistory,
    TaskPriority,
    TaskSource,
    TaskStatus,
    VALID_TRANSITIONS,
    _now_iso,
)
from jarvis.kanban.store import KanbanStore
from jarvis.utils.logging import get_logger

log = get_logger(__name__)


class InvalidTransition(Exception):
    """Raised when a status transition is not allowed."""

    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Cannot transition from {current} to {target}")
        self.current = current
        self.target = target


class TaskLimitExceeded(Exception):
    """Raised when auto-task creation limit is reached."""
    pass


class SubtaskDepthExceeded(Exception):
    """Raised when subtask nesting depth limit is reached."""
    pass


class KanbanEngine:
    """Core business logic for the Kanban board."""

    def __init__(
        self,
        store: KanbanStore,
        max_auto_tasks: int = 10,
        max_subtask_depth: int = 3,
        cascade_cancel: bool = True,
    ) -> None:
        self._store = store
        self._max_auto_tasks = max_auto_tasks
        self._max_subtask_depth = max_subtask_depth
        self._cascade_cancel = cascade_cancel
        self._auto_task_count = 0

    def create_task(
        self,
        title: str,
        *,
        description: str = "",
        priority: TaskPriority | str = TaskPriority.MEDIUM,
        assigned_agent: str = "",
        source: TaskSource | str = TaskSource.MANUAL,
        source_ref: str = "",
        parent_id: str = "",
        labels: list[str] | None = None,
        created_by: str = "user",
    ) -> Task:
        src = TaskSource(source) if isinstance(source, str) else source
        pri = TaskPriority(priority) if isinstance(priority, str) else priority

        # Guard: auto-task limit (manual tasks bypass)
        if src != TaskSource.MANUAL:
            if self._auto_task_count >= self._max_auto_tasks:
                raise TaskLimitExceeded(
                    f"Auto-task limit reached ({self._max_auto_tasks}). "
                    f"Reset with reset_auto_counter()."
                )
            self._auto_task_count += 1

        # Guard: subtask depth
        if parent_id:
            depth = self._get_depth(parent_id)
            if depth >= self._max_subtask_depth:
                raise SubtaskDepthExceeded(
                    f"Max subtask depth ({self._max_subtask_depth}) exceeded"
                )

        task = Task(
            title=title,
            description=description,
            status=TaskStatus.TODO,
            priority=pri,
            assigned_agent=assigned_agent,
            source=src,
            source_ref=source_ref,
            parent_id=parent_id,
            labels=labels or [],
            created_by=created_by,
        )
        self._store.create(task)
        log.info("kanban_task_created", task_id=task.id, title=title, source=src.value)
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self._store.get(task_id)

    def list_tasks(self, **filters: Any) -> list[Task]:
        return self._store.list_tasks(**filters)

    def update_task(self, task_id: str, changed_by: str = "user", **fields: Any) -> Task | None:
        task = self._store.get(task_id)
        if task is None:
            return None
        # If status change, use transition() instead
        if "status" in fields:
            new_status = TaskStatus(fields.pop("status"))
            self.transition(task_id, new_status, changed_by=changed_by)
        if fields:
            self._store.update(task_id, **fields)
        return self._store.get(task_id)

    def transition(
        self,
        task_id: str,
        new_status: TaskStatus | str,
        changed_by: str = "user",
        note: str = "",
    ) -> Task:
        task = self._store.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        target = TaskStatus(new_status) if isinstance(new_status, str) else new_status
        current = task.status

        # Validate transition
        allowed = VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTransition(current.value, target.value)

        # Update status
        update_fields: dict[str, Any] = {"status": target.value, "updated_at": _now_iso()}
        if target == TaskStatus.DONE:
            update_fields["completed_at"] = _now_iso()
        self._store.update(task_id, **update_fields)

        # Record history
        self._store.record_history(task_id, current.value, target.value, changed_by, note)

        # Cascade cancel to subtasks
        if target == TaskStatus.CANCELLED and self._cascade_cancel:
            for sub in self._store.get_subtasks(task_id):
                if sub.status not in (TaskStatus.DONE, TaskStatus.CANCELLED):
                    self.transition(sub.id, TaskStatus.CANCELLED, changed_by="system",
                                    note="Parent cancelled")

        # Check if all sibling subtasks are DONE → parent to VERIFYING
        if target == TaskStatus.DONE and task.parent_id:
            self._check_parent_completion(task.parent_id)

        return self._store.get(task_id)  # type: ignore[return-value]

    def delete_task(self, task_id: str) -> None:
        self._store.delete(task_id, cascade=True)
        log.info("kanban_task_deleted", task_id=task_id)

    def move_task(self, task_id: str, new_status: str, sort_order: int = 0,
                  changed_by: str = "user") -> Task | None:
        task = self._store.get(task_id)
        if task is None:
            return None
        target = TaskStatus(new_status)
        # Validate transition
        allowed = VALID_TRANSITIONS.get(task.status, set())
        if target not in allowed:
            raise InvalidTransition(task.status.value, target.value)
        self._store.record_history(task_id, task.status.value, target.value, changed_by, "drag-and-drop")
        return self._store.move(task_id, new_status, sort_order)

    def get_history(self, task_id: str) -> list[TaskHistory]:
        return self._store.get_history(task_id)

    def get_subtasks(self, task_id: str) -> list[Task]:
        return self._store.get_subtasks(task_id)

    def stats(self) -> dict[str, Any]:
        return self._store.stats()

    def reset_auto_counter(self) -> None:
        self._auto_task_count = 0

    def _get_depth(self, task_id: str) -> int:
        depth = 0
        current_id = task_id
        while current_id:
            task = self._store.get(current_id)
            if task is None:
                break
            depth += 1
            current_id = task.parent_id
        return depth

    def _check_parent_completion(self, parent_id: str) -> None:
        parent = self._store.get(parent_id)
        if parent is None or parent.status == TaskStatus.DONE:
            return
        subtasks = self._store.get_subtasks(parent_id)
        if not subtasks:
            return
        all_done = all(s.status == TaskStatus.DONE for s in subtasks)
        if all_done and parent.status == TaskStatus.IN_PROGRESS:
            self.transition(parent_id, TaskStatus.VERIFYING, changed_by="system",
                            note="All subtasks completed")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_kanban_engine.py -v`
Expected: ALL PASS (16 tests)

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/kanban/engine.py tests/test_kanban_engine.py
git commit -m "feat(kanban): KanbanEngine — transitions, guards, sub-task lifecycle"
```

---

### Task 5: Source Adapters

**Files:**
- Create: `src/jarvis/kanban/sources.py`
- Test: `tests/test_kanban_sources.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for Kanban task source adapters."""

from __future__ import annotations

import pytest

from jarvis.kanban.sources import ChatTaskDetector, CronTaskAdapter, EvolutionTaskAdapter, SystemTaskAdapter


class TestChatTaskDetector:
    def test_detect_german(self):
        result = ChatTaskDetector.detect("Erstelle einen Task: Recherchiere AI News")
        assert result is not None
        assert result["title"] == "Recherchiere AI News"

    def test_detect_english(self):
        result = ChatTaskDetector.detect("Create a task: Review security audit")
        assert result is not None
        assert result["title"] == "Review security audit"

    def test_detect_kanban_tag(self):
        result = ChatTaskDetector.detect("I will do this. [KANBAN:Fix login bug]")
        assert result is not None
        assert result["title"] == "Fix login bug"

    def test_no_detection(self):
        result = ChatTaskDetector.detect("What is the weather today?")
        assert result is None

    def test_detect_neuer_task(self):
        result = ChatTaskDetector.detect("Neuer Task: Datenbank optimieren")
        assert result is not None
        assert result["title"] == "Datenbank optimieren"


class TestCronTaskAdapter:
    def test_build_task_data(self):
        data = CronTaskAdapter.build_task_data(
            job_name="morning_briefing",
            result="Briefing erstellt: 5 News, 2 CVEs",
            follow_up=False,
        )
        assert data["title"] == "Cron: morning_briefing"
        assert data["source"] == "cron"
        assert data["source_ref"] == "morning_briefing"
        assert data["status"] == "done"

    def test_build_followup(self):
        data = CronTaskAdapter.build_task_data(
            job_name="security_scan",
            result="3 critical findings",
            follow_up=True,
        )
        assert data["status"] == "todo"
        assert "3 critical findings" in data["description"]


class TestEvolutionTaskAdapter:
    def test_skill_failure(self):
        data = EvolutionTaskAdapter.from_skill_failure("web_scraper", 0.4)
        assert "web_scraper" in data["title"]
        assert data["priority"] == "high"
        assert data["source"] == "evolution"

    def test_knowledge_gap(self):
        data = EvolutionTaskAdapter.from_knowledge_gap("quantum computing")
        assert "quantum computing" in data["title"]
        assert data["source"] == "evolution"


class TestSystemTaskAdapter:
    def test_from_recovery_failure(self):
        data = SystemTaskAdapter.from_recovery_failure("web_search", 3, "timeout")
        assert "web_search" in data["title"]
        assert data["priority"] == "urgent"
        assert data["source"] == "system"
```

- [ ] **Step 2: Implement sources.py**

```python
"""Task source adapters — detect and build tasks from various Cognithor subsystems."""

from __future__ import annotations

import re
from typing import Any


class ChatTaskDetector:
    """Detect task creation intent in chat messages / planner output."""

    _PATTERNS = [
        re.compile(r"\[KANBAN:(.+?)\]", re.IGNORECASE),
        re.compile(r"(?:erstelle|create)\s+(?:einen?\s+)?task:\s*(.+)", re.IGNORECASE),
        re.compile(r"(?:neuer|new)\s+task:\s*(.+)", re.IGNORECASE),
        re.compile(r"add\s+to\s+board:\s*(.+)", re.IGNORECASE),
    ]

    @classmethod
    def detect(cls, text: str) -> dict[str, str] | None:
        for pattern in cls._PATTERNS:
            m = pattern.search(text)
            if m:
                title = m.group(1).strip().rstrip(".")
                return {"title": title}
        return None


class CronTaskAdapter:
    """Build task data from cron job execution results."""

    @staticmethod
    def build_task_data(
        job_name: str,
        result: str,
        follow_up: bool = False,
    ) -> dict[str, Any]:
        return {
            "title": f"Cron: {job_name}",
            "description": result,
            "source": "cron",
            "source_ref": job_name,
            "status": "todo" if follow_up else "done",
            "priority": "medium" if follow_up else "low",
            "created_by": "system",
        }


class EvolutionTaskAdapter:
    """Build task data from evolution engine observations."""

    @staticmethod
    def from_skill_failure(skill_name: str, failure_rate: float) -> dict[str, Any]:
        return {
            "title": f"Optimize skill: {skill_name} ({failure_rate:.0%} failure rate)",
            "description": f"Skill '{skill_name}' has a {failure_rate:.0%} failure rate. "
                           f"Investigate root cause and improve.",
            "source": "evolution",
            "source_ref": f"skill:{skill_name}",
            "priority": "high" if failure_rate > 0.5 else "medium",
            "labels": ["optimization", "skill"],
            "created_by": "system",
        }

    @staticmethod
    def from_knowledge_gap(topic: str) -> dict[str, Any]:
        return {
            "title": f"Research: {topic}",
            "description": f"Knowledge gap detected for topic '{topic}'. "
                           f"Schedule deep research.",
            "source": "evolution",
            "source_ref": f"gap:{topic}",
            "priority": "medium",
            "labels": ["research", "knowledge-gap"],
            "created_by": "system",
        }


class SystemTaskAdapter:
    """Build task data from system events (recovery failures, errors)."""

    @staticmethod
    def from_recovery_failure(
        tool_name: str,
        attempts: int,
        error: str,
    ) -> dict[str, Any]:
        return {
            "title": f"Investigate: {tool_name} failures ({attempts}x)",
            "description": f"Tool '{tool_name}' failed {attempts} times. "
                           f"Last error: {error}. Recovery exhausted.",
            "source": "system",
            "source_ref": f"recovery:{tool_name}",
            "priority": "urgent",
            "labels": ["bug", "investigation"],
            "created_by": "system",
        }
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_kanban_sources.py -v`
Expected: ALL PASS (9 tests)

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/kanban/sources.py tests/test_kanban_sources.py
git commit -m "feat(kanban): source adapters — chat, cron, evolution, system"
```

---

### Task 6: REST API

**Files:**
- Create: `src/jarvis/kanban/api.py`
- Test: `tests/test_kanban_api.py`

- [ ] **Step 1: Write API tests**

```python
"""Tests for Kanban REST API."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jarvis.kanban.api import create_kanban_router
from jarvis.kanban.engine import KanbanEngine
from jarvis.kanban.store import KanbanStore


@pytest.fixture
def client(tmp_path):
    store = KanbanStore(str(tmp_path / "kanban.db"), use_encryption=False)
    engine = KanbanEngine(store)
    app = FastAPI()
    app.include_router(create_kanban_router(engine))
    return TestClient(app)


class TestKanbanAPI:
    def test_create_task(self, client):
        resp = client.post("/api/v1/kanban/tasks", json={
            "title": "Test task",
            "priority": "high",
            "assigned_agent": "coder",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test task"
        assert data["priority"] == "high"
        assert data["id"]

    def test_list_tasks(self, client):
        client.post("/api/v1/kanban/tasks", json={"title": "A"})
        client.post("/api/v1/kanban/tasks", json={"title": "B"})
        resp = client.get("/api/v1/kanban/tasks")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_filter_status(self, client):
        client.post("/api/v1/kanban/tasks", json={"title": "A"})
        resp = client.get("/api/v1/kanban/tasks", params={"status": "todo"})
        assert len(resp.json()) == 1
        resp2 = client.get("/api/v1/kanban/tasks", params={"status": "done"})
        assert len(resp2.json()) == 0

    def test_get_task(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Test"})
        task_id = r.json()["id"]
        resp = client.get(f"/api/v1/kanban/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test"

    def test_get_task_not_found(self, client):
        resp = client.get("/api/v1/kanban/tasks/nonexistent")
        assert resp.status_code == 404

    def test_update_task(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Old"})
        task_id = r.json()["id"]
        resp = client.patch(f"/api/v1/kanban/tasks/{task_id}", json={
            "title": "New",
            "assigned_agent": "researcher",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "New"

    def test_delete_task(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Delete"})
        task_id = r.json()["id"]
        resp = client.delete(f"/api/v1/kanban/tasks/{task_id}")
        assert resp.status_code == 204
        assert client.get(f"/api/v1/kanban/tasks/{task_id}").status_code == 404

    def test_move_task(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Move"})
        task_id = r.json()["id"]
        resp = client.post(f"/api/v1/kanban/tasks/{task_id}/move", json={
            "status": "in_progress",
            "sort_order": 3,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_move_invalid_transition(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Bad"})
        task_id = r.json()["id"]
        resp = client.post(f"/api/v1/kanban/tasks/{task_id}/move", json={
            "status": "done",
        })
        assert resp.status_code == 409

    def test_history(self, client):
        r = client.post("/api/v1/kanban/tasks", json={"title": "Track"})
        task_id = r.json()["id"]
        client.post(f"/api/v1/kanban/tasks/{task_id}/move", json={"status": "in_progress"})
        resp = client.get(f"/api/v1/kanban/tasks/{task_id}/history")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_stats(self, client):
        client.post("/api/v1/kanban/tasks", json={"title": "A"})
        client.post("/api/v1/kanban/tasks", json={"title": "B"})
        resp = client.get("/api/v1/kanban/stats")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
```

- [ ] **Step 2: Implement api.py**

```python
"""Kanban Board REST API — FastAPI router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from jarvis.kanban.engine import InvalidTransition, KanbanEngine, SubtaskDepthExceeded, TaskLimitExceeded
from jarvis.kanban.models import TaskPriority, TaskSource, TaskStatus
from jarvis.utils.logging import get_logger

log = get_logger(__name__)


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    assigned_agent: str = ""
    source: str = "manual"
    source_ref: str = ""
    parent_id: str = ""
    labels: list[str] = []


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    assigned_agent: str | None = None
    status: str | None = None
    labels: list[str] | None = None
    result_summary: str | None = None


class MoveTaskRequest(BaseModel):
    status: str
    sort_order: int = 0


def create_kanban_router(engine: KanbanEngine) -> APIRouter:
    router = APIRouter(prefix="/api/v1/kanban", tags=["kanban"])

    @router.post("/tasks", status_code=201)
    def create_task(req: CreateTaskRequest) -> dict[str, Any]:
        try:
            task = engine.create_task(
                title=req.title,
                description=req.description,
                priority=req.priority,
                assigned_agent=req.assigned_agent,
                source=req.source,
                source_ref=req.source_ref,
                parent_id=req.parent_id,
                labels=req.labels,
                created_by="user",
            )
            return task.to_dict()
        except TaskLimitExceeded as e:
            raise HTTPException(status_code=429, detail=str(e))
        except SubtaskDepthExceeded as e:
            raise HTTPException(status_code=422, detail=str(e))

    @router.get("/tasks")
    def list_tasks(
        status: str | None = None,
        agent: str | None = None,
        priority: str | None = None,
        source: str | None = None,
        parent_id: str | None = None,
        label: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = TaskStatus(status)
        if agent:
            filters["agent"] = agent
        if priority:
            filters["priority"] = TaskPriority(priority)
        if source:
            filters["source"] = TaskSource(source)
        if parent_id:
            filters["parent_id"] = parent_id
        if label:
            filters["label"] = label
        return [t.to_dict() for t in engine.list_tasks(**filters)]

    @router.get("/tasks/{task_id}")
    def get_task(task_id: str) -> dict[str, Any]:
        task = engine.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        result = task.to_dict()
        result["subtasks"] = [s.to_dict() for s in engine.get_subtasks(task_id)]
        return result

    @router.patch("/tasks/{task_id}")
    def update_task(task_id: str, req: UpdateTaskRequest) -> dict[str, Any]:
        fields = {k: v for k, v in req.model_dump().items() if v is not None}
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        try:
            task = engine.update_task(task_id, changed_by="user", **fields)
        except InvalidTransition as e:
            raise HTTPException(status_code=409, detail=str(e))
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.to_dict()

    @router.delete("/tasks/{task_id}", status_code=204)
    def delete_task(task_id: str) -> Response:
        engine.delete_task(task_id)
        return Response(status_code=204)

    @router.post("/tasks/{task_id}/move")
    def move_task(task_id: str, req: MoveTaskRequest) -> dict[str, Any]:
        try:
            task = engine.move_task(task_id, req.status, req.sort_order, changed_by="user")
        except InvalidTransition as e:
            raise HTTPException(status_code=409, detail=str(e))
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.to_dict()

    @router.get("/tasks/{task_id}/history")
    def get_history(task_id: str) -> list[dict[str, Any]]:
        history = engine.get_history(task_id)
        return [
            {
                "id": h.id,
                "task_id": h.task_id,
                "old_status": h.old_status,
                "new_status": h.new_status,
                "changed_by": h.changed_by,
                "changed_at": h.changed_at,
                "note": h.note,
            }
            for h in history
        ]

    @router.get("/stats")
    def get_stats() -> dict[str, Any]:
        return engine.stats()

    return router
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_kanban_api.py -v`
Expected: ALL PASS (11 tests)

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/kanban/api.py tests/test_kanban_api.py
git commit -m "feat(kanban): REST API — 10 endpoints with validation"
```

---

### Task 7: MCP Tools for Agents

**Files:**
- Create: `src/jarvis/mcp/kanban_tools.py`
- Test: `tests/test_kanban_tools.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for Kanban MCP tools."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jarvis.kanban.engine import KanbanEngine
from jarvis.kanban.models import TaskSource, TaskStatus
from jarvis.kanban.store import KanbanStore


@pytest.fixture
def engine(tmp_path):
    store = KanbanStore(str(tmp_path / "kanban.db"), use_encryption=False)
    return KanbanEngine(store)


class TestKanbanMCPTools:
    @pytest.mark.asyncio
    async def test_create_tool(self, engine):
        from jarvis.mcp.kanban_tools import _handle_create
        result = await _handle_create(engine, {
            "title": "Agent task",
            "description": "Found a bug",
            "priority": "high",
        })
        assert "Agent task" in result
        assert "created" in result.lower() or "task" in result.lower()

    @pytest.mark.asyncio
    async def test_update_tool(self, engine):
        task = engine.create_task("Test", created_by="agent")
        engine.transition(task.id, TaskStatus.IN_PROGRESS, changed_by="agent")
        from jarvis.mcp.kanban_tools import _handle_update
        result = await _handle_update(engine, {
            "task_id": task.id,
            "status": "verifying",
            "result_summary": "Done!",
        })
        assert "updated" in result.lower() or "verifying" in result.lower()

    @pytest.mark.asyncio
    async def test_list_tool(self, engine):
        engine.create_task("A", assigned_agent="coder", created_by="user")
        engine.create_task("B", assigned_agent="researcher", created_by="user")
        from jarvis.mcp.kanban_tools import _handle_list
        result = await _handle_list(engine, {"assigned_to_me": True}, agent_name="coder")
        assert "A" in result
        assert "B" not in result
```

- [ ] **Step 2: Implement kanban_tools.py**

```python
"""Kanban MCP tools — let agents create, update, and list tasks."""

from __future__ import annotations

from typing import Any

from jarvis.kanban.engine import KanbanEngine, TaskLimitExceeded
from jarvis.kanban.models import TaskSource, TaskStatus
from jarvis.utils.logging import get_logger

log = get_logger(__name__)


async def _handle_create(engine: KanbanEngine, params: dict[str, Any]) -> str:
    try:
        task = engine.create_task(
            title=params["title"],
            description=params.get("description", ""),
            priority=params.get("priority", "medium"),
            labels=params.get("labels", []),
            parent_id=params.get("parent_id", ""),
            source=TaskSource.AGENT,
            created_by=params.get("created_by", "agent"),
        )
        return f"Task created: '{task.title}' (ID: {task.id}, status: {task.status.value})"
    except TaskLimitExceeded as e:
        return f"Task creation blocked: {e}"


async def _handle_update(engine: KanbanEngine, params: dict[str, Any]) -> str:
    task_id = params["task_id"]
    task = engine.get_task(task_id)
    if task is None:
        return f"Task {task_id} not found"

    if "status" in params:
        try:
            engine.transition(task_id, params["status"], changed_by="agent")
        except Exception as e:
            return f"Status update failed: {e}"

    updates: dict[str, Any] = {}
    if "result_summary" in params:
        updates["result_summary"] = params["result_summary"]
    if updates:
        engine.update_task(task_id, changed_by="agent", **updates)

    updated = engine.get_task(task_id)
    return f"Task updated: '{updated.title}' → {updated.status.value}"


async def _handle_list(
    engine: KanbanEngine,
    params: dict[str, Any],
    agent_name: str = "",
) -> str:
    filters: dict[str, Any] = {}
    if params.get("status"):
        filters["status"] = TaskStatus(params["status"])
    if params.get("assigned_to_me") and agent_name:
        filters["agent"] = agent_name

    tasks = engine.list_tasks(**filters)
    if not tasks:
        return "No tasks found."

    lines = [f"Found {len(tasks)} task(s):"]
    for t in tasks[:20]:
        lines.append(f"  [{t.status.value}] {t.title} (ID: {t.id})")
    if len(tasks) > 20:
        lines.append(f"  ... and {len(tasks) - 20} more")
    return "\n".join(lines)


def register_kanban_tools(mcp_client: Any, engine: KanbanEngine) -> None:
    """Register Kanban MCP tools on the given MCP client."""

    async def create_handler(params: dict[str, Any]) -> str:
        return await _handle_create(engine, params)

    async def update_handler(params: dict[str, Any]) -> str:
        return await _handle_update(engine, params)

    async def list_handler(params: dict[str, Any]) -> str:
        return await _handle_list(engine, params)

    mcp_client.register_builtin_handler(
        "kanban_create_task",
        create_handler,
        description="Create a new task on the Kanban board",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description (Markdown)"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "labels": {"type": "array", "items": {"type": "string"}},
                "parent_id": {"type": "string", "description": "Parent task ID for sub-tasks"},
            },
            "required": ["title"],
        },
        risk_level="green",
    )

    mcp_client.register_builtin_handler(
        "kanban_update_task",
        update_handler,
        description="Update a task's status or result on the Kanban board",
        input_schema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID to update"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "verifying", "done", "blocked"]},
                "result_summary": {"type": "string", "description": "Result after completion"},
            },
            "required": ["task_id"],
        },
        risk_level="green",
    )

    mcp_client.register_builtin_handler(
        "kanban_list_tasks",
        list_handler,
        description="List tasks on the Kanban board",
        input_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["todo", "in_progress", "verifying", "done", "blocked"]},
                "assigned_to_me": {"type": "boolean", "description": "Only show tasks assigned to this agent"},
            },
        },
        risk_level="green",
    )
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_kanban_tools.py -v`
Expected: ALL PASS (3 tests)

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/mcp/kanban_tools.py tests/test_kanban_tools.py
git commit -m "feat(kanban): 3 MCP tools — agents can create, update, list tasks"
```

---

### Task 8: Wire into Gateway + Gatekeeper

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`
- Modify: `src/jarvis/core/gatekeeper.py`

- [ ] **Step 1: Add kanban tools to Gatekeeper GREEN list**

In `src/jarvis/core/gatekeeper.py`, in the `_classify_risk` method, add the 3 kanban tools to the `green_tools` set:

```python
            "kanban_create_task",
            "kanban_update_task",
            "kanban_list_tasks",
```

- [ ] **Step 2: Initialize KanbanEngine in gateway**

In `src/jarvis/gateway/gateway.py`, after the ATL tools registration (around line 820, before `gateway_init_complete`), add:

```python
        # Kanban Board
        try:
            if getattr(self._config, "kanban", None) and self._config.kanban.enabled:
                from jarvis.kanban.store import KanbanStore
                from jarvis.kanban.engine import KanbanEngine
                from jarvis.mcp.kanban_tools import register_kanban_tools

                _kanban_db = self._config.jarvis_home / "db" / "kanban.db"
                _kanban_store = KanbanStore(str(_kanban_db))
                self._kanban_engine = KanbanEngine(
                    _kanban_store,
                    max_auto_tasks=self._config.kanban.max_auto_tasks_per_session,
                    max_subtask_depth=self._config.kanban.max_subtask_depth,
                    cascade_cancel=self._config.kanban.cascade_cancel_subtasks,
                )
                register_kanban_tools(self._mcp_client, self._kanban_engine)
                log.info("kanban_engine_initialized", db=str(_kanban_db))
        except Exception:
            log.debug("kanban_init_failed", exc_info=True)
            self._kanban_engine = None
```

- [ ] **Step 3: Register Kanban API routes in __main__.py**

In `src/jarvis/__main__.py`, after the existing API route registrations (search for `community_marketplace_api_registered`), add:

```python
                # Kanban Board API
                try:
                    if hasattr(gateway, "_kanban_engine") and gateway._kanban_engine is not None:
                        from jarvis.kanban.api import create_kanban_router
                        api_app.include_router(create_kanban_router(gateway._kanban_engine))
                        log.info("kanban_api_registered")
                except Exception:
                    log.debug("kanban_api_registration_failed", exc_info=True)
```

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/gateway/gateway.py src/jarvis/core/gatekeeper.py src/jarvis/__main__.py
git commit -m "feat(kanban): wire engine + API + MCP tools into gateway"
```

---

### Task 9: Run All Tests

- [ ] **Step 1: Run the complete Kanban test suite**

```bash
pytest tests/test_kanban_models.py tests/test_kanban_store.py tests/test_kanban_engine.py tests/test_kanban_sources.py tests/test_kanban_api.py tests/test_kanban_tools.py -v
```

Expected: ALL PASS (~56 tests)

- [ ] **Step 2: Run Ruff lint check**

```bash
ruff check src/jarvis/kanban/ src/jarvis/mcp/kanban_tools.py tests/test_kanban_*.py --select=F821,F811 --no-fix
```

Expected: `All checks passed!`

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat(kanban): complete backend — models, store, engine, sources, API, MCP tools

- 6 new files in src/jarvis/kanban/
- 3 MCP tools for agent task management
- 10 REST endpoints
- SQLCipher-encrypted persistence
- 6 task sources (manual, chat, cron, evolution, agent, system)
- Sub-task lifecycle with cascade cancel
- Status transition enforcement with history
- Guards: max auto-tasks, max subtask depth
- ~56 tests"
```
