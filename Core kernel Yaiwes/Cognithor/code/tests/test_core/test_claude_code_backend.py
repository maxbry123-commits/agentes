"""Tests for the ClaudeCodeBackend (Claude Code CLI proxy)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.core.llm_backend import (
    ChatResponse,
    ClaudeCodeBackend,
    LLMBackendError,
    LLMBackendType,
)

# ============================================================================
# Basics
# ============================================================================


class TestClaudeCodeBackendBasics:
    def test_backend_type(self) -> None:
        b = ClaudeCodeBackend()
        assert b.backend_type == LLMBackendType.CLAUDE_CODE

    def test_default_model(self) -> None:
        b = ClaudeCodeBackend()
        assert b._model == "sonnet"

    def test_custom_model(self) -> None:
        b = ClaudeCodeBackend(model="opus", timeout=60)
        assert b._model == "opus"
        assert b._timeout == 60

    @pytest.mark.asyncio
    async def test_list_models(self) -> None:
        b = ClaudeCodeBackend()
        models = await b.list_models()
        assert "sonnet" in models
        assert "opus" in models
        assert "haiku" in models

    @pytest.mark.asyncio
    async def test_close_is_noop(self) -> None:
        b = ClaudeCodeBackend()
        await b.close()  # Should not raise


# ============================================================================
# _messages_to_prompt
# ============================================================================


class TestMessagesToPrompt:
    def test_single_user_message(self) -> None:
        b = ClaudeCodeBackend()
        result = b._messages_to_prompt([{"role": "user", "content": "Hello"}])
        assert "Hello" in result
        # Planner prefix + suffix are included
        assert "PLANNING MODULE" in result
        assert "REMINDER" in result

    def test_system_and_user(self) -> None:
        b = ClaudeCodeBackend()
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ]
        result = b._messages_to_prompt(msgs)
        # System messages use [Context] tag, not [System]
        assert "[Context]: You are helpful." in result
        assert "Hi" in result

    def test_assistant_message(self) -> None:
        b = ClaudeCodeBackend()
        msgs = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]
        result = b._messages_to_prompt(msgs)
        assert "[Previous response]: Hi there" in result
        assert "How are you?" in result

    def test_empty_messages(self) -> None:
        b = ClaudeCodeBackend()
        result = b._messages_to_prompt([])
        # Even with no messages, planner prefix + suffix included
        assert "PLANNING MODULE" in result

    def test_missing_content_key(self) -> None:
        b = ClaudeCodeBackend()
        result = b._messages_to_prompt([{"role": "user"}])
        assert "PLANNING MODULE" in result


# ============================================================================
# is_available
# ============================================================================


class TestIsAvailable:
    @pytest.mark.asyncio
    async def test_available_when_cli_exists(self) -> None:
        b = ClaudeCodeBackend()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"1.0.0", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            assert await b.is_available() is True

    @pytest.mark.asyncio
    async def test_unavailable_when_cli_missing(self) -> None:
        b = ClaudeCodeBackend()

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("claude not found"),
        ):
            assert await b.is_available() is False

    @pytest.mark.asyncio
    async def test_unavailable_on_nonzero_exit(self) -> None:
        b = ClaudeCodeBackend()

        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"error"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            assert await b.is_available() is False


# ============================================================================
# chat
# ============================================================================


class TestChat:
    @pytest.mark.asyncio
    async def test_chat_success(self) -> None:
        b = ClaudeCodeBackend(model="sonnet")

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(
            return_value=(b"Hello from Claude!", b""),
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await b.chat(
                "sonnet",
                [{"role": "user", "content": "Hi"}],
            )

        assert isinstance(result, ChatResponse)
        assert result.content == "Hello from Claude!"
        assert result.model == "sonnet"

    @pytest.mark.asyncio
    async def test_chat_uses_default_model_when_empty(self) -> None:
        b = ClaudeCodeBackend(model="opus")

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Response", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            result = await b.chat(
                "",
                [{"role": "user", "content": "Test"}],
            )

        assert result.model == "opus"
        # Check that --model opus was passed
        call_args = mock_exec.call_args
        cmd_list = call_args[0]
        model_idx = list(cmd_list).index("--model")
        assert cmd_list[model_idx + 1] == "opus"

    @pytest.mark.asyncio
    async def test_chat_json_format(self) -> None:
        b = ClaudeCodeBackend()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b'{"key": "value"}', b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            await b.chat(
                "sonnet",
                [{"role": "user", "content": "JSON please"}],
                format_json=True,
            )

        call_args = mock_exec.call_args
        cmd_list = list(call_args[0])
        # Should have --output-format json
        fmt_idx = cmd_list.index("--output-format")
        assert cmd_list[fmt_idx + 1] == "json"

    @pytest.mark.asyncio
    async def test_chat_text_format(self) -> None:
        b = ClaudeCodeBackend()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"text response", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            await b.chat(
                "sonnet",
                [{"role": "user", "content": "Plain text"}],
                format_json=False,
            )

        call_args = mock_exec.call_args
        cmd_list = list(call_args[0])
        fmt_idx = cmd_list.index("--output-format")
        assert cmd_list[fmt_idx + 1] == "text"


# ============================================================================
# Error handling
# ============================================================================


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_cli_error_raises_backend_error(self) -> None:
        b = ClaudeCodeBackend()

        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(
            return_value=(b"", b"Authentication failed"),
        )

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(LLMBackendError, match="Claude CLI Fehler"),
        ):
            await b.chat("sonnet", [{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_cli_error_includes_exit_code(self) -> None:
        b = ClaudeCodeBackend()

        mock_proc = AsyncMock()
        mock_proc.returncode = 42
        mock_proc.communicate = AsyncMock(return_value=(b"", b"bad"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            try:
                await b.chat("sonnet", [{"role": "user", "content": "Hi"}])
            except LLMBackendError as exc:
                assert exc.status_code == 42
            else:
                pytest.fail("Expected LLMBackendError")

    @pytest.mark.asyncio
    async def test_cli_not_found_raises_backend_error(self) -> None:
        b = ClaudeCodeBackend()

        with (
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=FileNotFoundError("not found"),
            ),
            pytest.raises(LLMBackendError, match="Claude CLI nicht gefunden"),
        ):
            await b.chat("sonnet", [{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_timeout_raises_backend_error(self) -> None:
        b = ClaudeCodeBackend(timeout=1)

        mock_proc = AsyncMock()

        async def slow_communicate(input=None):
            await asyncio.sleep(10)
            return (b"", b"")

        mock_proc.communicate = slow_communicate

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            patch(
                "asyncio.wait_for",
                side_effect=TimeoutError(),
            ),
            pytest.raises(LLMBackendError, match="Timeout"),
        ):
            await b.chat("sonnet", [{"role": "user", "content": "Hi"}])


# ============================================================================
# embed (not supported)
# ============================================================================


class TestEmbed:
    @pytest.mark.asyncio
    async def test_embed_raises_not_implemented(self) -> None:
        b = ClaudeCodeBackend()
        with pytest.raises(LLMBackendError, match="Embeddings"):
            await b.embed("sonnet", "some text")


# ============================================================================
# chat_stream
# ============================================================================


class TestChatStream:
    @pytest.mark.asyncio
    async def test_stream_yields_lines(self) -> None:
        b = ClaudeCodeBackend()

        lines = [b"Hello ", b"world\n", b"How are you?\n"]
        line_iter = iter(lines)

        mock_stdout = AsyncMock()

        async def readline():
            try:
                return next(line_iter)
            except StopIteration:
                return b""

        mock_stdout.readline = readline

        mock_stdin = AsyncMock()
        mock_stdin.write = MagicMock()
        mock_stdin.drain = AsyncMock()
        mock_stdin.close = MagicMock()

        mock_stderr = AsyncMock()
        mock_stderr.read = AsyncMock(return_value=b"")

        mock_proc = AsyncMock()
        mock_proc.stdin = mock_stdin
        mock_proc.stdout = mock_stdout
        mock_proc.stderr = mock_stderr
        mock_proc.returncode = 0
        mock_proc.wait = AsyncMock(return_value=0)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            chunks = []
            async for chunk in b.chat_stream(
                "sonnet",
                [{"role": "user", "content": "Hi"}],
            ):
                chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0] == "Hello "
        assert chunks[1] == "world\n"

    @pytest.mark.asyncio
    async def test_stream_cli_not_found(self) -> None:
        b = ClaudeCodeBackend()

        with (
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=FileNotFoundError("not found"),
            ),
            pytest.raises(LLMBackendError, match="Claude CLI nicht gefunden"),
        ):
            async for _ in b.chat_stream(
                "sonnet",
                [{"role": "user", "content": "Hi"}],
            ):
                pass
