"""Tests for jarvis.core.llm_retry — retry logic with stream-to-sync fallback."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from cognithor.core.llm_backend import LLMBackendError
from cognithor.core.llm_retry import (
    BASE_DELAY_MS,
    is_retryable_error,
    retry_llm_call,
    should_fallback_stream_to_sync,
)

# ============================================================================
# is_retryable_error
# ============================================================================


class TestIsRetryableError:
    """Test transient-error classification."""

    @pytest.mark.parametrize(
        "msg",
        [
            "fetch failed",
            "Network unreachable",
            "Connection timed out",
            "socket hang up",
            "ECONNRESET by peer",
            "ECONNREFUSED 127.0.0.1:11434",
            "EAI_AGAIN dns resolution",
            "timeout waiting for response",
        ],
    )
    def test_message_patterns_are_retryable(self, msg: str) -> None:
        assert is_retryable_error(RuntimeError(msg)) is True

    @pytest.mark.parametrize(
        "msg",
        [
            "invalid JSON in response",
            "model not found",
            "context length exceeded",
            "",
        ],
    )
    def test_non_transient_messages_are_not_retryable(self, msg: str) -> None:
        assert is_retryable_error(RuntimeError(msg)) is False

    @pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
    def test_status_code_retryable(self, status: int) -> None:
        err = LLMBackendError("server error", status_code=status)
        assert is_retryable_error(err) is True

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
    def test_status_code_not_retryable(self, status: int) -> None:
        err = LLMBackendError("client error", status_code=status)
        assert is_retryable_error(err) is False

    def test_status_code_none_falls_through_to_message(self) -> None:
        err = LLMBackendError("timeout", status_code=None)
        assert is_retryable_error(err) is True

    def test_plain_exception_without_status_code(self) -> None:
        assert is_retryable_error(ValueError("timeout")) is True
        assert is_retryable_error(ValueError("bad value")) is False


# ============================================================================
# should_fallback_stream_to_sync
# ============================================================================


class TestShouldFallbackStreamToSync:
    """Streaming fallback excludes rate-limit errors."""

    def test_rate_limit_429_excluded(self) -> None:
        err = LLMBackendError("too many requests", status_code=429)
        assert should_fallback_stream_to_sync(err) is False

    def test_rate_limit_message_excluded(self) -> None:
        err = RuntimeError("rate limit exceeded")
        assert should_fallback_stream_to_sync(err) is False

    def test_network_error_eligible(self) -> None:
        err = RuntimeError("ECONNRESET")
        assert should_fallback_stream_to_sync(err) is True

    def test_timeout_eligible(self) -> None:
        err = LLMBackendError("timed out", status_code=504)
        assert should_fallback_stream_to_sync(err) is True

    def test_non_retryable_not_eligible(self) -> None:
        err = RuntimeError("model not found")
        assert should_fallback_stream_to_sync(err) is False


# ============================================================================
# retry_llm_call
# ============================================================================


class TestRetryLlmCall:
    """Async retry wrapper tests."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self) -> None:
        fn = AsyncMock(return_value="ok")
        result = await retry_llm_call(fn)
        assert result == "ok"
        assert fn.await_count == 1

    @pytest.mark.asyncio
    async def test_success_after_transient_failure(self) -> None:
        fn = AsyncMock(
            side_effect=[RuntimeError("ECONNRESET"), "recovered"],
        )
        result = await retry_llm_call(fn)
        assert result == "recovered"
        assert fn.await_count == 2

    @pytest.mark.asyncio
    async def test_non_retryable_error_raises_immediately(self) -> None:
        fn = AsyncMock(side_effect=RuntimeError("model not found"))
        with pytest.raises(RuntimeError, match="model not found"):
            await retry_llm_call(fn)
        assert fn.await_count == 1

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_raises(self) -> None:
        fn = AsyncMock(side_effect=RuntimeError("timeout"))
        with pytest.raises(RuntimeError, match="timeout"):
            await retry_llm_call(fn, max_retries=3)
        assert fn.await_count == 3

    @pytest.mark.asyncio
    async def test_respects_max_retries_param(self) -> None:
        fn = AsyncMock(side_effect=RuntimeError("ECONNREFUSED"))
        with pytest.raises(RuntimeError):
            await retry_llm_call(fn, max_retries=2)
        assert fn.await_count == 2

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self) -> None:
        """Verify that retries add some delay (coarse timing check)."""
        fn = AsyncMock(
            side_effect=[
                RuntimeError("timeout"),
                RuntimeError("timeout"),
                "ok",
            ],
        )
        t0 = asyncio.get_event_loop().time()
        result = await retry_llm_call(fn, max_retries=3)
        elapsed = asyncio.get_event_loop().time() - t0
        assert result == "ok"
        # First delay = 200ms, second = 400ms -> total >= 0.5s
        min_expected = (BASE_DELAY_MS + BASE_DELAY_MS * 2) / 1000 * 0.8
        assert elapsed >= min_expected


# ============================================================================
# Stream-to-sync fallback
# ============================================================================


class TestStreamFallback:
    """Test the stream_fallback_fn path."""

    @pytest.mark.asyncio
    async def test_fallback_invoked_after_retries_exhausted(self) -> None:
        call_fn = AsyncMock(side_effect=RuntimeError("ECONNRESET"))
        fallback_fn = AsyncMock(return_value="sync_result")

        result = await retry_llm_call(
            call_fn,
            max_retries=2,
            stream_fallback_fn=fallback_fn,
        )
        assert result == "sync_result"
        assert call_fn.await_count == 2
        fallback_fn.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fallback_not_invoked_for_rate_limit(self) -> None:
        call_fn = AsyncMock(
            side_effect=LLMBackendError("too many requests", status_code=429),
        )
        fallback_fn = AsyncMock(return_value="sync_result")

        with pytest.raises(LLMBackendError):
            await retry_llm_call(
                call_fn,
                max_retries=2,
                stream_fallback_fn=fallback_fn,
            )
        fallback_fn.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fallback_failure_raises_fallback_error(self) -> None:
        call_fn = AsyncMock(side_effect=RuntimeError("ECONNRESET"))
        fallback_fn = AsyncMock(side_effect=RuntimeError("fallback also failed"))

        with pytest.raises(RuntimeError, match="fallback also failed"):
            await retry_llm_call(
                call_fn,
                max_retries=1,
                stream_fallback_fn=fallback_fn,
            )

    @pytest.mark.asyncio
    async def test_no_fallback_when_not_provided(self) -> None:
        call_fn = AsyncMock(side_effect=RuntimeError("ECONNRESET"))

        with pytest.raises(RuntimeError, match="ECONNRESET"):
            await retry_llm_call(call_fn, max_retries=2)
