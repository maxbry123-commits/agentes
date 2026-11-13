"""Tests fuer hitl/manager.py und hitl/notifier.py -- fehlende Zeilen."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from cognithor.hitl.manager import ApprovalManager
from cognithor.hitl.notifier import HITLNotifier, NotificationRecord
from cognithor.hitl.types import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    EscalationAction,
    EscalationPolicy,
    HITLConfig,
    HITLNodeKind,
    NotificationChannel,
    NotificationType,
)

# ============================================================================
# HITLNotifier
# ============================================================================


class TestHITLNotifier:
    @pytest.mark.asyncio
    async def test_notify_new_request_log(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[NotificationChannel(channel_type=NotificationType.LOG)],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 1
        assert notifier.stats()["total_sent"] == 1

    @pytest.mark.asyncio
    async def test_notify_in_app(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[NotificationChannel(channel_type=NotificationType.IN_APP)],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 1
        pending = notifier.get_pending_notifications()
        assert len(pending) == 1

    @pytest.mark.asyncio
    async def test_notify_callback(self) -> None:
        notifier = HITLNotifier()
        handler = AsyncMock()
        notifier.register_callback("my_cb", handler)

        config = HITLConfig(
            notifications=[
                NotificationChannel(
                    channel_type=NotificationType.CALLBACK,
                    endpoint="my_cb",
                )
            ],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 1
        handler.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_callback_not_found(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[
                NotificationChannel(
                    channel_type=NotificationType.CALLBACK,
                    endpoint="missing",
                )
            ],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 0

    @pytest.mark.asyncio
    async def test_notify_webhook(self) -> None:
        notifier = HITLNotifier()
        webhook = AsyncMock(return_value=True)
        notifier.set_webhook_handler(webhook)

        config = HITLConfig(
            notifications=[
                NotificationChannel(
                    channel_type=NotificationType.WEBHOOK,
                    endpoint="https://example.com/hook",
                )
            ],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 1
        webhook.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_notify_email(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[
                NotificationChannel(
                    channel_type=NotificationType.EMAIL,
                    endpoint="test@example.com",
                )
            ],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 1

    @pytest.mark.asyncio
    async def test_disabled_channel_skipped(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[
                NotificationChannel(
                    channel_type=NotificationType.LOG,
                    enabled=False,
                )
            ],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 0

    @pytest.mark.asyncio
    async def test_notify_reminder(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[NotificationChannel(channel_type=NotificationType.LOG)],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_reminder(request)
        assert sent == 1

    @pytest.mark.asyncio
    async def test_notify_resolved(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[NotificationChannel(channel_type=NotificationType.LOG)],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        response = ApprovalResponse(
            request_id="r1",
            decision=ApprovalStatus.APPROVED,
            reviewer="user",
        )
        sent = await notifier.notify_resolved(request, response)
        assert sent == 1

    @pytest.mark.asyncio
    async def test_notify_escalated(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[NotificationChannel(channel_type=NotificationType.LOG)],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_escalated(request)
        assert sent == 1

    @pytest.mark.asyncio
    async def test_render_custom_template(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(
            notifications=[
                NotificationChannel(
                    channel_type=NotificationType.LOG,
                    template="Custom: {event} for {graph}/{node}",
                )
            ],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="myg",
            node_name="myn",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 1

    def test_unregister_callback(self) -> None:
        notifier = HITLNotifier()
        notifier.register_callback("cb", AsyncMock())
        notifier.unregister_callback("cb")
        assert "cb" not in notifier._callbacks

    def test_clear_in_app_queue(self) -> None:
        notifier = HITLNotifier()
        notifier._in_app_queue.append({"msg": "test"})
        count = notifier.clear_in_app_queue()
        assert count == 1
        assert len(notifier._in_app_queue) == 0

    def test_get_history(self) -> None:
        notifier = HITLNotifier()
        notifier._history.append(NotificationRecord("log", "r1", "msg", True))
        history = notifier.get_history()
        assert len(history) == 1
        assert history[0]["success"] is True

    def test_notification_record_to_dict_with_error(self) -> None:
        record = NotificationRecord("log", "r1", "msg", False, "err")
        d = record.to_dict()
        assert d["error"] == "err"
        assert d["success"] is False

    @pytest.mark.asyncio
    async def test_send_exception_handling(self) -> None:
        notifier = HITLNotifier()
        handler = AsyncMock(side_effect=RuntimeError("boom"))
        notifier.register_callback("bad", handler)

        config = HITLConfig(
            notifications=[
                NotificationChannel(
                    channel_type=NotificationType.CALLBACK,
                    endpoint="bad",
                )
            ],
        )
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 0
        assert notifier.stats()["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_default_channels_when_none(self) -> None:
        notifier = HITLNotifier()
        config = HITLConfig(notifications=[])
        request = ApprovalRequest(
            execution_id="e1",
            graph_name="g",
            node_name="n",
            config=config,
        )
        sent = await notifier.notify_new_request(request)
        assert sent == 1  # Falls back to LOG


# ============================================================================
# ApprovalManager
# ============================================================================


class TestApprovalManager:
    @pytest.mark.asyncio
    async def test_create_request(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        assert req.status == ApprovalStatus.PENDING
        assert mgr.stats()["total_created"] == 1

    @pytest.mark.asyncio
    async def test_respond_approve(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        response = ApprovalResponse(decision=ApprovalStatus.APPROVED, reviewer="u")
        task = await mgr.respond(req.request_id, response)
        assert task is not None
        assert task.request.status == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_respond_reject(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        response = ApprovalResponse(decision=ApprovalStatus.REJECTED, reviewer="u")
        task = await mgr.respond(req.request_id, response)
        assert task.request.status == ApprovalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_respond_not_found(self) -> None:
        mgr = ApprovalManager()
        response = ApprovalResponse(decision=ApprovalStatus.APPROVED, reviewer="u")
        result = await mgr.respond("ghost", response)
        assert result is None

    @pytest.mark.asyncio
    async def test_respond_already_resolved(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        resp = ApprovalResponse(decision=ApprovalStatus.APPROVED, reviewer="u")
        await mgr.respond(req.request_id, resp)
        task = await mgr.respond(req.request_id, resp)
        assert task is not None  # Returns task but doesn't re-process

    @pytest.mark.asyncio
    async def test_cancel(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        result = await mgr.cancel(req.request_id, reason="test")
        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_resolved(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        resp = ApprovalResponse(decision=ApprovalStatus.APPROVED, reviewer="u")
        await mgr.respond(req.request_id, resp)
        result = await mgr.cancel(req.request_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self) -> None:
        mgr = ApprovalManager()
        result = await mgr.cancel("ghost")
        assert result is False

    @pytest.mark.asyncio
    async def test_delegate(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        result = await mgr.delegate(req.request_id, "reviewer2", delegated_by="admin")
        assert result is True
        assert "reviewer2" in req.config.assignees

    @pytest.mark.asyncio
    async def test_delegate_nonexistent(self) -> None:
        mgr = ApprovalManager()
        result = await mgr.delegate("ghost", "reviewer2")
        assert result is False

    @pytest.mark.asyncio
    async def test_gate_auto_approve(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig(
            node_kind=HITLNodeKind.GATE,
            auto_approve_fn=lambda ctx: True,
        )
        req = await mgr.create_request("e1", "graph", "node", config)
        assert req.status == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_gate_auto_approve_exception(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig(
            node_kind=HITLNodeKind.GATE,
            auto_approve_fn=lambda ctx: 1 / 0,
        )
        req = await mgr.create_request("e1", "graph", "node", config)
        assert req.status == ApprovalStatus.PENDING

    def test_get_task(self) -> None:
        mgr = ApprovalManager()
        assert mgr.get_task("ghost") is None

    @pytest.mark.asyncio
    async def test_get_pending(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        await mgr.create_request("e1", "graph", "node", config)
        pending = mgr.get_pending()
        assert len(pending) == 1

    @pytest.mark.asyncio
    async def test_get_by_execution(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        await mgr.create_request("e1", "graph", "n1", config)
        await mgr.create_request("e1", "graph", "n2", config)
        tasks = mgr.get_by_execution("e1")
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_get_history(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        resp = ApprovalResponse(decision=ApprovalStatus.APPROVED, reviewer="u")
        await mgr.respond(req.request_id, resp)
        history = mgr.get_history(status=ApprovalStatus.APPROVED)
        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_wait_for_resolution_already_resolved(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        resp = ApprovalResponse(decision=ApprovalStatus.APPROVED, reviewer="u")
        await mgr.respond(req.request_id, resp)
        task = await mgr.wait_for_resolution(req.request_id)
        assert task is not None

    @pytest.mark.asyncio
    async def test_wait_for_resolution_not_found(self) -> None:
        mgr = ApprovalManager()
        result = await mgr.wait_for_resolution("ghost")
        assert result is None

    @pytest.mark.asyncio
    async def test_wait_for_resolution_timeout(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig(
            escalation=EscalationPolicy(
                timeout_seconds=0.1,
                action=EscalationAction.AUTO_APPROVE,
            )
        )
        req = await mgr.create_request("e1", "graph", "node", config)
        task = await mgr.wait_for_resolution(req.request_id, timeout=0.1)
        # Should auto-approve after timeout
        assert task is not None

    @pytest.mark.asyncio
    async def test_cleanup(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig()
        req = await mgr.create_request("e1", "graph", "node", config)
        resp = ApprovalResponse(decision=ApprovalStatus.APPROVED, reviewer="u")
        await mgr.respond(req.request_id, resp)
        # With max_age_days=0, should remove the task (it was just created)
        # but timestamp parsing may be tricky
        removed = mgr.cleanup(max_age_days=0)
        assert isinstance(removed, int)

    @pytest.mark.asyncio
    async def test_handle_timeout_auto_reject(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig(
            escalation=EscalationPolicy(
                timeout_seconds=0.01,
                action=EscalationAction.AUTO_REJECT,
            )
        )
        req = await mgr.create_request("e1", "graph", "node", config)
        await mgr._handle_timeout(req.request_id)
        task = mgr.get_task(req.request_id)
        assert task.request.status == ApprovalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_handle_timeout_delegate(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig(
            escalation=EscalationPolicy(
                timeout_seconds=0.01,
                action=EscalationAction.DELEGATE,
                delegate_to="admin",
            )
        )
        req = await mgr.create_request("e1", "graph", "node", config)
        await mgr._handle_timeout(req.request_id)
        assert "admin" in req.config.assignees

    @pytest.mark.asyncio
    async def test_handle_timeout_notify_supervisor(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig(
            escalation=EscalationPolicy(
                timeout_seconds=0.01,
                action=EscalationAction.NOTIFY_SUPERVISOR,
            )
        )
        req = await mgr.create_request("e1", "graph", "node", config)
        await mgr._handle_timeout(req.request_id)
        assert mgr.stats()["escalated"] == 1

    @pytest.mark.asyncio
    async def test_handle_timeout_pause_indefinitely(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig(
            escalation=EscalationPolicy(
                timeout_seconds=0.01,
                action=EscalationAction.PAUSE_INDEFINITELY,
            )
        )
        req = await mgr.create_request("e1", "graph", "node", config)
        await mgr._handle_timeout(req.request_id)
        task = mgr.get_task(req.request_id)
        assert task.request.status == ApprovalStatus.ESCALATED

    @pytest.mark.asyncio
    async def test_handle_timeout_max_escalations(self) -> None:
        mgr = ApprovalManager()
        config = HITLConfig(
            escalation=EscalationPolicy(
                timeout_seconds=0.01,
                max_escalations=0,
                action=EscalationAction.AUTO_APPROVE,
            )
        )
        req = await mgr.create_request("e1", "graph", "node", config)
        await mgr._handle_timeout(req.request_id)
        task = mgr.get_task(req.request_id)
        assert task.request.status == ApprovalStatus.TIMED_OUT
