"""Tests for Kanban MCP tools."""

from __future__ import annotations

import pytest

from cognithor.kanban.engine import KanbanEngine
from cognithor.kanban.models import TaskStatus
from cognithor.kanban.store import KanbanStore


@pytest.fixture
def engine(tmp_path):
    store = KanbanStore(str(tmp_path / "kanban.db"), use_encryption=False)
    return KanbanEngine(store)


class TestKanbanMCPTools:
    @pytest.mark.asyncio
    async def test_create_tool(self, engine):
        from cognithor.mcp.kanban_tools import _handle_create

        result = await _handle_create(
            engine,
            {
                "title": "Agent task",
                "description": "Found a bug",
                "priority": "high",
            },
        )
        assert "Agent task" in result
        assert "created" in result.lower() or "task" in result.lower()

    @pytest.mark.asyncio
    async def test_update_tool(self, engine):
        task = engine.create_task("Test", created_by="agent")
        engine.transition(task.id, TaskStatus.IN_PROGRESS, changed_by="agent")
        from cognithor.mcp.kanban_tools import _handle_update

        result = await _handle_update(
            engine,
            {
                "task_id": task.id,
                "status": "verifying",
                "result_summary": "Done!",
            },
        )
        assert "updated" in result.lower() or "verifying" in result.lower()

    @pytest.mark.asyncio
    async def test_list_tool(self, engine):
        engine.create_task("A", assigned_agent="coder", created_by="user")
        engine.create_task("B", assigned_agent="researcher", created_by="user")
        from cognithor.mcp.kanban_tools import _handle_list

        result = await _handle_list(engine, {"assigned_to_me": True}, agent_name="coder")
        assert "A" in result
        assert "B" not in result
