"""Tests fuer telemetry/instrumentation.py -- trace/measure decorators + TelemetryHub."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cognithor.telemetry.instrumentation import TelemetryHub, measure, trace

# ============================================================================
# trace decorator
# ============================================================================


class TestTraceDecorator:
    def test_sync_function(self) -> None:
        tracer = MagicMock()
        span = MagicMock()
        span.__enter__ = MagicMock(return_value=span)
        span.__exit__ = MagicMock(return_value=False)
        tracer.start_span.return_value = span

        @trace(tracer, "test_span")
        def my_func(x: int) -> int:
            return x * 2

        result = my_func(5)
        assert result == 10
        tracer.start_span.assert_called_once()
        span.set_ok.assert_called_once()

    def test_sync_function_error(self) -> None:
        tracer = MagicMock()
        span = MagicMock()
        span.__enter__ = MagicMock(return_value=span)
        span.__exit__ = MagicMock(return_value=False)
        tracer.start_span.return_value = span

        @trace(tracer, "error_span")
        def bad_func() -> None:
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            bad_func()
        span.set_error.assert_called_once_with("boom")

    @pytest.mark.asyncio
    async def test_async_function(self) -> None:
        tracer = MagicMock()
        span = MagicMock()
        span.__enter__ = MagicMock(return_value=span)
        span.__exit__ = MagicMock(return_value=False)
        tracer.start_span.return_value = span

        @trace(tracer, "async_span")
        async def my_async(x: int) -> int:
            return x + 1

        result = await my_async(3)
        assert result == 4
        span.set_ok.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_function_error(self) -> None:
        tracer = MagicMock()
        span = MagicMock()
        span.__enter__ = MagicMock(return_value=span)
        span.__exit__ = MagicMock(return_value=False)
        tracer.start_span.return_value = span

        @trace(tracer, "async_error")
        async def bad_async() -> None:
            raise RuntimeError("async boom")

        with pytest.raises(RuntimeError, match="async boom"):
            await bad_async()
        span.set_error.assert_called_once()

    def test_default_name_from_qualname(self) -> None:
        tracer = MagicMock()
        span = MagicMock()
        span.__enter__ = MagicMock(return_value=span)
        span.__exit__ = MagicMock(return_value=False)
        tracer.start_span.return_value = span

        @trace(tracer)
        def named_func() -> None:
            pass

        named_func()
        call_args = tracer.start_span.call_args
        assert "named_func" in call_args[0][0]


# ============================================================================
# measure decorator
# ============================================================================


class TestMeasureDecorator:
    def test_sync_measure(self) -> None:
        metrics = MagicMock()

        @measure(metrics, "latency_ms", "calls_total", label="test")
        def my_func() -> str:
            return "ok"

        result = my_func()
        assert result == "ok"
        metrics.histogram.assert_called_once()
        metrics.counter.assert_called_once()

    def test_sync_measure_error(self) -> None:
        metrics = MagicMock()

        @measure(metrics, "latency_ms", "calls_total")
        def bad_func() -> None:
            raise ValueError("err")

        with pytest.raises(ValueError):
            bad_func()
        metrics.histogram.assert_called_once()
        metrics.counter.assert_called_once()
        # Check status=error
        _, kwargs = metrics.counter.call_args
        assert kwargs["status"] == "error"

    @pytest.mark.asyncio
    async def test_async_measure(self) -> None:
        metrics = MagicMock()

        @measure(metrics, "latency_ms", "calls_total")
        async def my_async() -> str:
            return "async_ok"

        result = await my_async()
        assert result == "async_ok"
        metrics.histogram.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_measure_error(self) -> None:
        metrics = MagicMock()

        @measure(metrics, "latency_ms", "calls_total")
        async def bad_async() -> None:
            raise RuntimeError("err")

        with pytest.raises(RuntimeError):
            await bad_async()
        metrics.histogram.assert_called_once()

    def test_measure_no_counter(self) -> None:
        metrics = MagicMock()

        @measure(metrics, "latency_ms")
        def no_counter() -> str:
            return "ok"

        no_counter()
        metrics.histogram.assert_called_once()
        metrics.counter.assert_not_called()


# ============================================================================
# TelemetryHub
# ============================================================================


class TestTelemetryHub:
    def test_default_init(self) -> None:
        hub = TelemetryHub()
        assert hub.tracer is not None
        assert hub.metrics is not None

    def test_custom_tracer_and_metrics(self) -> None:
        tracer = MagicMock()
        metrics = MagicMock()
        hub = TelemetryHub(tracer=tracer, metrics=metrics)
        assert hub.tracer is tracer
        assert hub.metrics is metrics

    def test_trace_request(self) -> None:
        hub = TelemetryHub()
        span = hub.trace_request("GET", "/api/test")
        assert span is not None

    def test_trace_request_with_headers(self) -> None:
        hub = TelemetryHub()
        span = hub.trace_request("POST", "/api/data", headers={"X-Trace": "abc"})
        assert span is not None

    def test_trace_llm_call(self) -> None:
        hub = TelemetryHub()
        span = hub.trace_llm_call("gpt-4", prompt_length=100)
        assert span is not None

    def test_trace_tool_call(self) -> None:
        hub = TelemetryHub()
        span = hub.trace_tool_call("read_file")
        assert span is not None

    def test_trace_graph_execution(self) -> None:
        hub = TelemetryHub()
        span = hub.trace_graph_execution("etl_pipeline")
        assert span is not None

    def test_trace_a2a_message_outbound(self) -> None:
        hub = TelemetryHub()
        span = hub.trace_a2a_message("agent-2", direction="outbound")
        assert span is not None

    def test_trace_a2a_message_inbound(self) -> None:
        hub = TelemetryHub()
        span = hub.trace_a2a_message("agent-2", direction="inbound")
        assert span is not None

    def test_trace_browser_action(self) -> None:
        hub = TelemetryHub()
        span = hub.trace_browser_action("click", url="https://example.com")
        assert span is not None

    def test_record_request(self) -> None:
        hub = TelemetryHub()
        hub.record_request("GET", 200, 50.0)
        hub.record_request("POST", 500, 100.0)  # error

    def test_record_llm_usage(self) -> None:
        hub = TelemetryHub()
        hub.record_llm_usage("claude", 100.0, input_tokens=500, output_tokens=200)

    def test_record_llm_usage_no_tokens(self) -> None:
        hub = TelemetryHub()
        hub.record_llm_usage("gpt", 50.0)

    def test_record_graph_execution(self) -> None:
        hub = TelemetryHub()
        hub.record_graph_execution("etl", 200.0, status="completed")

    def test_set_active_sessions(self) -> None:
        hub = TelemetryHub()
        hub.set_active_sessions(5)

    def test_dashboard_snapshot(self) -> None:
        hub = TelemetryHub()
        snapshot = hub.dashboard_snapshot()
        assert "service" in snapshot
        assert "tracer" in snapshot
        assert "metrics" in snapshot

    def test_shutdown(self) -> None:
        hub = TelemetryHub()
        hub.shutdown()  # Should not crash

    def test_stats(self) -> None:
        hub = TelemetryHub()
        stats = hub.stats()
        assert "tracer" in stats
        assert "metrics" in stats
