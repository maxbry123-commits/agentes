"""KanbanEngine — business logic for task management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cognithor.kanban.models import (
    VALID_TRANSITIONS,
    Task,
    TaskHistory,
    TaskPriority,
    TaskSource,
    TaskStatus,
    _now_iso,
)
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.kanban.store import KanbanStore

log = get_logger(__name__)


class InvalidTransition(Exception):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Cannot transition from {current} to {target}")
        self.current = current
        self.target = target


class TaskLimitExceeded(Exception):
    pass


class SubtaskDepthExceeded(Exception):
    pass


class KanbanEngine:
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
        status: TaskStatus | str = TaskStatus.TODO,
        assigned_agent: str = "",
        source: TaskSource | str = TaskSource.MANUAL,
        source_ref: str = "",
        parent_id: str = "",
        labels: list[str] | None = None,
        created_by: str = "user",
    ) -> Task:
        src = TaskSource(source) if isinstance(source, str) else source
        pri = TaskPriority(priority) if isinstance(priority, str) else priority
        sts = TaskStatus(status) if isinstance(status, str) else status

        if src != TaskSource.MANUAL:
            if self._auto_task_count >= self._max_auto_tasks:
                raise TaskLimitExceeded(
                    f"Auto-task limit reached ({self._max_auto_tasks}). "
                    f"Reset with reset_auto_counter()."
                )
            self._auto_task_count += 1

        if parent_id:
            depth = self._get_depth(parent_id)
            if depth > self._max_subtask_depth:
                raise SubtaskDepthExceeded(
                    f"Max subtask depth ({self._max_subtask_depth}) exceeded"
                )

        task = Task(
            title=title,
            description=description,
            status=sts,
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

        allowed = VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTransition(current.value, target.value)

        update_fields: dict[str, Any] = {"status": target.value, "updated_at": _now_iso()}
        if target == TaskStatus.DONE:
            update_fields["completed_at"] = _now_iso()
        self._store.update(task_id, **update_fields)

        self._store.record_history(task_id, current.value, target.value, changed_by, note)

        if target == TaskStatus.CANCELLED and self._cascade_cancel:
            for sub in self._store.get_subtasks(task_id):
                if sub.status not in (TaskStatus.DONE, TaskStatus.CANCELLED):
                    self.transition(
                        sub.id, TaskStatus.CANCELLED, changed_by="system", note="Parent cancelled"
                    )

        if target == TaskStatus.DONE and task.parent_id:
            self._check_parent_completion(task.parent_id)

        return self._store.get(task_id) or task  # fallback to pre-update task

    def delete_task(self, task_id: str) -> None:
        self._store.delete(task_id, cascade=True)
        log.info("kanban_task_deleted", task_id=task_id)

    def move_task(
        self, task_id: str, new_status: str, sort_order: int = 0, changed_by: str = "user"
    ) -> Task | None:
        task = self._store.get(task_id)
        if task is None:
            return None
        target = TaskStatus(new_status)
        allowed = VALID_TRANSITIONS.get(task.status, set())
        if target not in allowed:
            raise InvalidTransition(task.status.value, target.value)
        self._store.record_history(
            task_id, task.status.value, target.value, changed_by, "drag-and-drop"
        )
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
            self.transition(
                parent_id, TaskStatus.VERIFYING, changed_by="system", note="All subtasks completed"
            )
