"""Tests for a2a/server.py and a2a/adapter.py -- Coverage boost."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from cognithor.a2a.server import A2AServer, A2AServerConfig
from cognithor.a2a.types import (
    A2A_PROTOCOL_VERSION,
    A2AAgentCard,
    A2AErrorCode,
    Message,
    MessageRole,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

# ============================================================================
# A2AServer -- dispatch Tests
# ============================================================================


class TestA2AServerDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_unknown_method(self):
        server = A2AServer()
        result = await server.dispatch("unknown/method")
        assert "error" in result
        assert result["error"]["code"] == A2AErrorCode.METHOD_NOT_FOUND

    @pytest.mark.asyncio
    async def test_dispatch_message_send_new_task(self):
        server = A2AServer()
        msg = Message(role=MessageRole.USER, parts=[TextPart(text="Hello")])
        result = await server.dispatch("message/send", {"message": msg.to_dict()})
        assert "id" in result
        assert "status" in result

    @pytest.mark.asyncio
    async def test_dispatch_message_send_existing_task(self):
        server = A2AServer()
        # Create first task
        msg = Message(role=MessageRole.USER, parts=[TextPart(text="Hello")])
        r1 = await server.dispatch("message/send", {"message": msg.to_dict()})
        task_id = r1["id"]

        # Send message to existing task
        msg2 = Message(role=MessageRole.USER, parts=[TextPart(text="More")])
        r2 = await server.dispatch(
            "message/send",
            {
                "id": task_id,
                "message": msg2.to_dict(),
            },
        )
        assert r2["id"] == task_id

    @pytest.mark.asyncio
    async def test_dispatch_tasks_send_legacy(self):
        """Legacy tasks/send alias."""
        server = A2AServer()
        result = await server.dispatch(
            "tasks/send",
            {
                "message": {"role": "user", "parts": [{"type": "text", "text": "hi"}]},
            },
        )
        assert "id" in result

    @pytest.mark.asyncio
    async def test_dispatch_exception_in_handler(self):
        server = A2AServer()

        async def bad_handler(task):
            raise RuntimeError("Handler crash")

        server.set_task_handler(bad_handler)
        # Force an error by mocking _handle_message_send to raise
        with patch.object(server, "_handle_message_send", side_effect=RuntimeError("Test")):
            result = await server.dispatch("message/send", {})
        assert "error" in result
        assert result["error"]["code"] == A2AErrorCode.INTERNAL_ERROR


# ============================================================================
# A2AServer -- message/send Tests
# ============================================================================


class TestA2AServerMessageSend:
    @pytest.mark.asyncio
    async def test_max_tasks_reached(self):
        cfg = A2AServerConfig(max_tasks=1)
        server = A2AServer(cfg)
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("message/send", {"message": msg})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_send_to_completed_task(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        task_id = r["id"]
        # Manually complete the task (SUBMITTED -> WORKING -> COMPLETED)
        task = server.get_task(task_id)
        task.transition(TaskState.WORKING)
        task.transition(TaskState.COMPLETED)
        # Try sending to completed task
        r2 = await server.dispatch("message/send", {"id": task_id, "message": msg})
        assert "error" in r2

    @pytest.mark.asyncio
    async def test_send_with_metadata(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        result = await server.dispatch(
            "message/send",
            {
                "message": msg,
                "metadata": {"key": "val"},
                "contextId": "ctx1",
            },
        )
        assert "id" in result

    @pytest.mark.asyncio
    async def test_send_with_handler(self):
        """With task_handler, task is submitted and executed in background."""

        async def handler(task):
            task.transition(TaskState.COMPLETED)
            return task

        server = A2AServer()
        server.set_task_handler(handler)
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        result = await server.dispatch("message/send", {"message": msg})
        assert "id" in result
        # Give the background task time to complete
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_send_to_input_required_task(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r1 = await server.dispatch("message/send", {"message": msg})
        task = server.get_task(r1["id"])
        task.transition(TaskState.INPUT_REQUIRED)
        r2 = await server.dispatch("message/send", {"id": r1["id"], "message": msg})
        assert r2["id"] == r1["id"]


# ============================================================================
# A2AServer -- tasks/get Tests
# ============================================================================


class TestA2AServerTasksGet:
    @pytest.mark.asyncio
    async def test_get_existing_task(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("tasks/get", {"id": r["id"]})
        assert result["id"] == r["id"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self):
        server = A2AServer()
        result = await server.dispatch("tasks/get", {"id": "ghost"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_with_history_length(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("tasks/get", {"id": r["id"], "historyLength": 5})
        assert "id" in result

    @pytest.mark.asyncio
    async def test_get_with_zero_history_length(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("tasks/get", {"id": r["id"], "historyLength": 0})
        # history key should be removed
        assert "history" not in result or result.get("history") is None


# ============================================================================
# A2AServer -- tasks/list Tests
# ============================================================================


class TestA2AServerTasksList:
    @pytest.mark.asyncio
    async def test_list_all(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        await server.dispatch("message/send", {"message": msg})
        await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("tasks/list", {})
        assert result["total"] == 2
        assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_list_by_context(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        await server.dispatch("message/send", {"message": msg, "contextId": "ctx1"})
        await server.dispatch("message/send", {"message": msg, "contextId": "ctx2"})
        result = await server.dispatch("tasks/list", {"contextId": "ctx1"})
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_list_by_state_string(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("tasks/list", {"state": "submitted"})
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_by_state_list(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("tasks/list", {"state": ["submitted", "working"]})
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_with_offset_limit(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        for _ in range(5):
            await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("tasks/list", {"limit": 2, "offset": 1})
        assert len(result["tasks"]) == 2
        assert result["total"] == 5


# ============================================================================
# A2AServer -- tasks/cancel Tests
# ============================================================================


class TestA2AServerTasksCancel:
    @pytest.mark.asyncio
    async def test_cancel_success(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch("tasks/cancel", {"id": r["id"]})
        assert result.get("status", {}).get("state") == "canceled"

    @pytest.mark.asyncio
    async def test_cancel_not_found(self):
        server = A2AServer()
        result = await server.dispatch("tasks/cancel", {"id": "ghost"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_cancel_already_completed(self):
        server = A2AServer()
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        task = server.get_task(r["id"])
        task.transition(TaskState.WORKING)
        task.transition(TaskState.COMPLETED)
        result = await server.dispatch("tasks/cancel", {"id": r["id"]})
        assert "error" in result


# ============================================================================
# A2AServer -- Push Notification CRUD Tests
# ============================================================================


class TestA2AServerPush:
    @pytest.mark.asyncio
    async def test_push_disabled(self):
        server = A2AServer(A2AServerConfig(enable_push=False))
        result = await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": "t1",
                "url": "https://example.com/callback",
            },
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_push_create_success(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": r["id"],
                "url": "https://callback.example.com/hook",
            },
        )
        assert "configId" in result or "config_id" in result

    @pytest.mark.asyncio
    async def test_push_create_missing_params(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        result = await server.dispatch("tasks/pushNotification/create", {})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_push_create_bad_url(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": r["id"],
                "url": "ftp://bad.com/hook",
            },
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_push_create_invalid_hostname(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": r["id"],
                "url": "https:///no-host",
            },
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_push_create_task_not_found(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        result = await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": "ghost",
                "url": "https://callback.example.com/hook",
            },
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_push_create_with_auth(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        result = await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": r["id"],
                "url": "https://callback.example.com/hook",
                "authentication": {"type": "bearer", "credentials": "tok123"},
            },
        )
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_push_get(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        cr = await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": r["id"],
                "url": "https://callback.example.com/hook",
            },
        )
        config_id = cr.get("configId") or cr.get("config_id")
        result = await server.dispatch("tasks/pushNotification/get", {"configId": config_id})
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_push_get_not_found(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        result = await server.dispatch("tasks/pushNotification/get", {"configId": "ghost"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_push_list(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": r["id"],
                "url": "https://cb.example.com/hook1",
            },
        )
        result = await server.dispatch("tasks/pushNotification/list", {"taskId": r["id"]})
        assert len(result["configs"]) == 1

    @pytest.mark.asyncio
    async def test_push_list_all(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        result = await server.dispatch("tasks/pushNotification/list", {})
        assert "configs" in result

    @pytest.mark.asyncio
    async def test_push_delete(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        msg = {"role": "user", "parts": [{"type": "text", "text": "hi"}]}
        r = await server.dispatch("message/send", {"message": msg})
        cr = await server.dispatch(
            "tasks/pushNotification/create",
            {
                "taskId": r["id"],
                "url": "https://cb.example.com/hook",
            },
        )
        config_id = cr.get("configId") or cr.get("config_id")
        result = await server.dispatch("tasks/pushNotification/delete", {"configId": config_id})
        assert result.get("deleted") is True

    @pytest.mark.asyncio
    async def test_push_delete_not_found(self):
        server = A2AServer(A2AServerConfig(enable_push=True))
        result = await server.dispatch("tasks/pushNotification/delete", {"configId": "ghost"})
        assert "error" in result


# ============================================================================
# A2AServer -- process_jsonrpc / handle_http_request Tests
# ============================================================================


class TestA2AServerHTTP:
    @pytest.mark.asyncio
    async def test_process_jsonrpc_with_id(self):
        server = A2AServer()
        result = await server.process_jsonrpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tasks/list",
                "params": {},
            }
        )
        assert result["jsonrpc"] == "2.0"
        assert "result" in result

    @pytest.mark.asyncio
    async def test_process_jsonrpc_notification(self):
        """JSON-RPC notification (no id) returns None."""
        server = A2AServer()
        result = await server.process_jsonrpc(
            {
                "method": "tasks/list",
                "params": {},
            }
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_process_jsonrpc_error(self):
        server = A2AServer()
        result = await server.process_jsonrpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "unknown",
            }
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_http_request_auth_required(self):
        cfg = A2AServerConfig(require_auth=True, auth_token="secret")
        server = A2AServer(cfg)
        result = await server.handle_http_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tasks/list"},
            auth_token="wrong",
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_http_request_auth_success(self):
        cfg = A2AServerConfig(require_auth=True, auth_token="secret")
        server = A2AServer(cfg)
        result = await server.handle_http_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tasks/list", "params": {}},
            auth_token="secret",
        )
        assert "result" in result

    @pytest.mark.asyncio
    async def test_handle_http_request_incompatible_version(self):
        server = A2AServer()
        result = await server.handle_http_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tasks/list"},
            client_version="99.0.0",
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_http_request_compatible_version(self):
        server = A2AServer()
        result = await server.handle_http_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tasks/list", "params": {}},
            client_version=A2A_PROTOCOL_VERSION,
        )
        assert "result" in result


# ============================================================================
# A2AServer -- Extended Card Tests
# ============================================================================


class TestA2AServerExtendedCard:
    @pytest.mark.asyncio
    async def test_extended_card(self):
        server = A2AServer()
        result = await server.dispatch("agent/authenticatedExtendedCard", {})
        assert result.get("authenticated") is True
        assert "activeTaskCount" in result


# ============================================================================
# A2AServer -- Task Execution Tests
# ============================================================================


class TestA2AServerTaskExecution:
    @pytest.mark.asyncio
    async def test_execute_task_no_handler(self):
        server = A2AServer()
        task = Task.create(message=Message(role=MessageRole.USER, parts=[TextPart(text="hi")]))
        server._tasks[task.id] = task
        await server._execute_task(task)
        assert task.state == TaskState.FAILED

    @pytest.mark.asyncio
    async def test_execute_task_handler_success(self):
        async def handler(task):
            task.transition(TaskState.COMPLETED)
            return task

        server = A2AServer()
        server.set_task_handler(handler)
        task = Task.create(message=Message(role=MessageRole.USER, parts=[TextPart(text="hi")]))
        server._tasks[task.id] = task
        await server._execute_task(task)
        assert server._tasks_completed == 1

    @pytest.mark.asyncio
    async def test_execute_task_handler_exception(self):
        async def handler(task):
            raise RuntimeError("Boom")

        server = A2AServer()
        server.set_task_handler(handler)
        task = Task.create(message=Message(role=MessageRole.USER, parts=[TextPart(text="hi")]))
        server._tasks[task.id] = task
        await server._execute_task(task)
        assert task.state == TaskState.FAILED
        assert server._tasks_failed == 1

    @pytest.mark.asyncio
    async def test_execute_task_timeout(self):
        async def slow_handler(task):
            await asyncio.sleep(100)
            return task

        cfg = A2AServerConfig(task_timeout_seconds=0.01)
        server = A2AServer(cfg)
        server.set_task_handler(slow_handler)
        task = Task.create(message=Message(role=MessageRole.USER, parts=[TextPart(text="hi")]))
        server._tasks[task.id] = task
        await server._execute_task(task)
        assert task.state == TaskState.FAILED

    @pytest.mark.asyncio
    async def test_handle_task_exception_callback(self):
        server = A2AServer()
        # _make_task_done_callback needs an a2a Task for the closure
        a2a_task = Task.create(message=Message(role=MessageRole.USER, parts=[TextPart(text="x")]))
        a2a_task._state = TaskState.WORKING
        server._tasks_failed = 0
        callback = server._make_task_done_callback(a2a_task)

        # Create a mock asyncio.Task with exception
        mock_task = MagicMock()
        mock_task.cancelled.return_value = False
        mock_task.exception.return_value = RuntimeError("test")
        callback(mock_task)  # should transition task to FAILED
        assert server._tasks_failed == 1

        # Cancelled task
        mock_task2 = MagicMock()
        mock_task2.cancelled.return_value = True
        callback(mock_task2)  # should return early

        # No exception
        mock_task3 = MagicMock()
        mock_task3.cancelled.return_value = False
        mock_task3.exception.return_value = None
        callback(mock_task3)


# ============================================================================
# A2AServer -- Streaming Tests
# ============================================================================


class TestA2AServerStreaming:
    @pytest.mark.asyncio
    async def test_stream_auth_failure(self):
        cfg = A2AServerConfig(require_auth=True, auth_token="secret")
        server = A2AServer(cfg)
        events = []
        async for ev in server.handle_stream_request({}, auth_token="wrong"):
            events.append(ev)
        assert len(events) == 1
        assert "error" in events[0]

    @pytest.mark.asyncio
    async def test_stream_with_task_handler(self):
        async def handler(task):
            task.transition(TaskState.COMPLETED)
            return task

        server = A2AServer()
        server.set_task_handler(handler)
        body = {"params": {"message": {"role": "user", "parts": [{"type": "text", "text": "hi"}]}}}
        events = []
        async for ev in server.handle_stream_request(body):
            events.append(ev)
        assert len(events) >= 2  # initial status + final status

    @pytest.mark.asyncio
    async def test_stream_with_stream_handler(self):
        async def stream_handler(task):
            yield TaskStatusUpdateEvent(
                task_id=task.id,
                context_id=task.context_id,
                status=TaskStatus(state=TaskState.COMPLETED),
                final=True,
            )

        server = A2AServer()
        server.set_stream_handler(stream_handler)
        body = {"params": {"message": {"role": "user", "parts": [{"type": "text", "text": "hi"}]}}}
        events = []
        async for ev in server.handle_stream_request(body):
            events.append(ev)
        assert len(events) >= 2

    @pytest.mark.asyncio
    async def test_stream_handler_exception(self):
        async def bad_stream_handler(task):
            raise RuntimeError("Stream error")
            yield  # make it an async generator

        server = A2AServer()
        server.set_stream_handler(bad_stream_handler)
        body = {"params": {"message": {"role": "user", "parts": [{"type": "text", "text": "hi"}]}}}
        events = []
        async for ev in server.handle_stream_request(body):
            events.append(ev)
        # Should get initial status + error status
        assert len(events) >= 2

    @pytest.mark.asyncio
    async def test_stream_task_handler_exception(self):
        async def bad_handler(task):
            raise RuntimeError("Handler error")

        server = A2AServer()
        server.set_task_handler(bad_handler)
        body = {"params": {"message": {"role": "user", "parts": [{"type": "text", "text": "hi"}]}}}
        events = []
        async for ev in server.handle_stream_request(body):
            events.append(ev)
        assert len(events) >= 2


# ============================================================================
# A2AServer -- Lifecycle / Stats Tests
# ============================================================================


class TestA2AServerLifecycle:
    @pytest.mark.asyncio
    async def test_start_disabled(self):
        server = A2AServer(A2AServerConfig(enabled=False))
        await server.start()
        assert server.is_running is False

    @pytest.mark.asyncio
    async def test_start_enabled(self):
        server = A2AServer(A2AServerConfig(enabled=True))
        await server.start()
        assert server.is_running is True
        await server.stop()
        assert server.is_running is False

    def test_get_task(self):
        server = A2AServer()
        assert server.get_task("ghost") is None

    def test_active_tasks(self):
        server = A2AServer()
        assert server.active_tasks() == []

    def test_cleanup_completed(self):
        server = A2AServer()
        task = Task.create()
        task.transition(TaskState.WORKING)
        task.transition(TaskState.COMPLETED)
        # Set timestamp to a past time to ensure cleanup picks it up
        task.status = TaskStatus(state=TaskState.COMPLETED, timestamp="2000-01-01T00:00:00Z")
        server._tasks[task.id] = task
        removed = server.cleanup_completed(max_age_seconds=0)
        assert removed >= 1

    def test_stats(self):
        server = A2AServer()
        s = server.stats()
        assert "enabled" in s
        assert "total_tasks" in s

    def test_get_agent_card_default(self):
        server = A2AServer(A2AServerConfig(agent_name="TestAgent"))
        card = server.get_agent_card()
        assert card["name"] == "TestAgent"

    def test_get_agent_card_custom(self):
        server = A2AServer()
        custom = A2AAgentCard(name="Custom")
        server.set_agent_card(custom)
        card = server.get_agent_card()
        assert card["name"] == "Custom"


# ============================================================================
# A2AAdapter Tests
# ============================================================================


class TestA2AAdapter:
    def _make_config(self, a2a_enabled=True, tmp_path=None):
        """Create a mock CognithorConfig."""

        config = MagicMock()
        mcp_path = MagicMock()
        mcp_path.exists.return_value = False
        config.mcp_config_file = mcp_path
        return config

    def test_setup_disabled(self):
        from cognithor.a2a.adapter import A2AAdapter

        config = self._make_config()
        adapter = A2AAdapter(config)
        result = adapter.setup()
        assert result is False
        assert adapter.enabled is False

    def test_setup_enabled_from_yaml(self, tmp_path):
        import yaml

        from cognithor.a2a.adapter import A2AAdapter

        mcp_yaml = tmp_path / "mcp.yaml"
        mcp_yaml.write_text(yaml.dump({"a2a": {"enabled": True, "port": 3099}}))
        config = MagicMock()
        config.mcp_config_file = mcp_yaml
        adapter = A2AAdapter(config)
        result = adapter.setup()
        assert result is True
        assert adapter.enabled is True
        assert adapter.server is not None
        assert adapter.client is not None

    def test_setup_with_interop(self, tmp_path):
        import yaml

        from cognithor.a2a.adapter import A2AAdapter

        mcp_yaml = tmp_path / "mcp.yaml"
        mcp_yaml.write_text(yaml.dump({"a2a": {"enabled": True}}))
        config = MagicMock()
        config.mcp_config_file = mcp_yaml
        config.owner_name = "Test"

        interop = MagicMock()
        interop.local_agent_id = "local"
        local_agent = MagicMock()
        interop.get_agent.return_value = local_agent
        interop.capabilities.get_capabilities.return_value = []

        adapter = A2AAdapter(config)
        result = adapter.setup(interop=interop)
        assert result is True

    @pytest.mark.asyncio
    async def test_start_stop(self, tmp_path):
        import yaml

        from cognithor.a2a.adapter import A2AAdapter

        mcp_yaml = tmp_path / "mcp.yaml"
        mcp_yaml.write_text(yaml.dump({"a2a": {"enabled": True}}))
        config = MagicMock()
        config.mcp_config_file = mcp_yaml

        adapter = A2AAdapter(config)
        adapter.setup()
        await adapter.start()
        assert adapter.server.is_running is True
        await adapter.stop()
        assert adapter.server.is_running is False

    @pytest.mark.asyncio
    async def test_handle_incoming_task_no_text(self, tmp_path):
        import yaml

        from cognithor.a2a.adapter import A2AAdapter

        mcp_yaml = tmp_path / "mcp.yaml"
        mcp_yaml.write_text(yaml.dump({"a2a": {"enabled": True}}))
        config = MagicMock()
        config.mcp_config_file = mcp_yaml
        adapter = A2AAdapter(config)
        adapter.setup()

        task = Task.create()  # no message
        result = await adapter._handle_incoming_task(task)
        assert result.state == TaskState.FAILED

    @pytest.mark.asyncio
    async def test_handle_incoming_task_echo(self, tmp_path):
        import yaml

        from cognithor.a2a.adapter import A2AAdapter

        mcp_yaml = tmp_path / "mcp.yaml"
        mcp_yaml.write_text(yaml.dump({"a2a": {"enabled": True}}))
        config = MagicMock()
        config.mcp_config_file = mcp_yaml
        adapter = A2AAdapter(config)
        adapter.setup()

        msg = Message(role=MessageRole.USER, parts=[TextPart(text="Hello")])
        task = Task.create(message=msg)
        # Pre-transition to WORKING (as _execute_task does)
        task.transition(TaskState.WORKING)
        result = await adapter._handle_incoming_task(task)
        assert result.state == TaskState.COMPLETED
        assert len(result.artifacts) > 0

    @pytest.mark.asyncio
    async def test_handle_incoming_task_with_handler(self, tmp_path):
        import yaml

        from cognithor.a2a.adapter import A2AAdapter

        mcp_yaml = tmp_path / "mcp.yaml"
        mcp_yaml.write_text(yaml.dump({"a2a": {"enabled": True}}))
        config = MagicMock()
        config.mcp_config_file = mcp_yaml

        async def handler(text, session_id="", channel=""):
            return "Processed"

        adapter = A2AAdapter(config)
        adapter.setup(message_handler=handler)

        msg = Message(role=MessageRole.USER, parts=[TextPart(text="Hello")])
        task = Task.create(message=msg)
        task.transition(TaskState.WORKING)
        result = await adapter._handle_incoming_task(task)
        assert result.state == TaskState.COMPLETED

    @pytest.mark.asyncio
    async def test_handle_incoming_task_handler_exception(self, tmp_path):
        import yaml

        from cognithor.a2a.adapter import A2AAdapter

        mcp_yaml = tmp_path / "mcp.yaml"
        mcp_yaml.write_text(yaml.dump({"a2a": {"enabled": True}}))
        config = MagicMock()
        config.mcp_config_file = mcp_yaml

        async def bad_handler(text, session_id="", channel=""):
            raise RuntimeError("Boom")

        adapter = A2AAdapter(config)
        adapter.setup(message_handler=bad_handler)

        msg = Message(role=MessageRole.USER, parts=[TextPart(text="Hello")])
        task = Task.create(message=msg)
        task.transition(TaskState.WORKING)
        result = await adapter._handle_incoming_task(task)
        assert result.state == TaskState.FAILED

    @pytest.mark.asyncio
    async def test_delegate_task_no_client(self, tmp_path):
        from cognithor.a2a.adapter import A2AAdapter

        config = MagicMock()
        config.mcp_config_file = MagicMock()
        config.mcp_config_file.exists.return_value = False
        adapter = A2AAdapter(config)
        result = await adapter.delegate_task("http://remote.local", "Hello")
        assert result is None

    @pytest.mark.asyncio
    async def test_discover_remote_no_client(self, tmp_path):
        from cognithor.a2a.adapter import A2AAdapter

        config = MagicMock()
        config.mcp_config_file = MagicMock()
        config.mcp_config_file.exists.return_value = False
        adapter = A2AAdapter(config)
        result = await adapter.discover_remote("http://remote.local")
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_a2a_request_no_server(self):
        from cognithor.a2a.adapter import A2AAdapter

        config = MagicMock()
        config.mcp_config_file = MagicMock()
        config.mcp_config_file.exists.return_value = False
        adapter = A2AAdapter(config)
        result = await adapter.handle_a2a_request({"jsonrpc": "2.0", "id": 1, "method": "test"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_stream_request_no_server(self):
        from cognithor.a2a.adapter import A2AAdapter

        config = MagicMock()
        config.mcp_config_file = MagicMock()
        config.mcp_config_file.exists.return_value = False
        adapter = A2AAdapter(config)
        events = []
        async for ev in adapter.handle_stream_request({}):
            events.append(ev)
        assert len(events) >= 1
        assert "error" in events[0]

    def test_get_agent_card_no_server(self):
        from cognithor.a2a.adapter import A2AAdapter

        config = MagicMock()
        config.mcp_config_file = MagicMock()
        config.mcp_config_file.exists.return_value = False
        adapter = A2AAdapter(config)
        result = adapter.get_agent_card()
        assert "error" in result

    def test_stats(self, tmp_path):
        import yaml

        from cognithor.a2a.adapter import A2AAdapter

        mcp_yaml = tmp_path / "mcp.yaml"
        mcp_yaml.write_text(yaml.dump({"a2a": {"enabled": True}}))
        config = MagicMock()
        config.mcp_config_file = mcp_yaml
        adapter = A2AAdapter(config)
        adapter.setup()
        s = adapter.stats()
        assert "enabled" in s
        assert "server" in s
        assert "client" in s


# ============================================================================
# capabilities_to_skills Tests
# ============================================================================


class TestCapabilitiesToSkills:
    def test_known_capability(self):
        from cognithor.a2a.adapter import capabilities_to_skills

        cap = MagicMock()
        cap.capability_type.value = "web_search"
        cap.description = ""
        cap.languages = ["de"]
        skills = capabilities_to_skills([cap])
        assert len(skills) == 1
        assert skills[0].id == "web_search"
        assert "de" in skills[0].tags

    def test_unknown_capability(self):
        from cognithor.a2a.adapter import capabilities_to_skills

        cap = MagicMock()
        cap.capability_type.value = "custom_thing"
        cap.description = "Custom"
        cap.languages = []
        skills = capabilities_to_skills([cap])
        assert len(skills) == 1
        assert skills[0].name == "custom_thing"
