"""Kanban Board REST API — FastAPI router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from cognithor.kanban.engine import (
    InvalidTransition,
    KanbanEngine,
    SubtaskDepthExceeded,
    TaskLimitExceeded,
)
from cognithor.kanban.models import TaskPriority, TaskSource, TaskStatus
from cognithor.utils.logging import get_logger

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
            raise HTTPException(status_code=429, detail=str(e)) from e
        except SubtaskDepthExceeded as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

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
            raise HTTPException(status_code=409, detail=str(e)) from e
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
            raise HTTPException(status_code=409, detail=str(e)) from e
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

    class ReorderRequest(BaseModel):
        items: list[dict[str, Any]]

    @router.post("/tasks/reorder")
    def reorder_tasks(req: ReorderRequest) -> dict[str, Any]:
        """Batch-update sort_order for tasks within a column.

        Body: {"items": [{"id": "abc", "sort_order": 0}, ...]}
        """
        updated = 0
        for item in req.items:
            task_id = item.get("id", "")
            sort_order = item.get("sort_order", 0)
            if task_id:
                task = engine.update_task(task_id, changed_by="user", sort_order=sort_order)
                if task is not None:
                    updated += 1
        return {"updated": updated}

    return router
