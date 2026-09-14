"""Kanban MCP tools — let agents create, update, and list tasks."""

from __future__ import annotations

from typing import Any

from cognithor.kanban.engine import KanbanEngine, TaskLimitExceeded
from cognithor.kanban.models import TaskSource, TaskStatus
from cognithor.utils.logging import get_logger

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
    if updated is None:
        return f"Task {task_id} updated but no longer found"
    return f"Task updated: '{updated.title}' -> {updated.status.value}"


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
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "verifying", "done", "blocked"],
                },
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
                "status": {
                    "type": "string",
                    "enum": ["todo", "in_progress", "verifying", "done", "blocked"],
                },
                "assigned_to_me": {
                    "type": "boolean",
                    "description": "Only show tasks assigned to this agent",
                },
            },
        },
        risk_level="green",
    )
