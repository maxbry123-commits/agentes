"""Error-path tests guarding the Observer's fail-open contract."""

from __future__ import annotations

import asyncio
import sqlite3
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from cognithor.config import CognithorConfig
from cognithor.core.observer import ObserverAudit
from cognithor.core.observer_store import AuditStore

if TYPE_CHECKING:
    from pathlib import Path

# Reusable all-pass JSON payload (all four dimensions present and passing).
_DIM = '"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""'
_ALL_PASS_JSON = (
    "{"
    f'"hallucination":  {{{_DIM}}},'
    f'"sycophancy":     {{{_DIM}}},'
    f'"laziness":       {{{_DIM}}},'
    f'"tool_ignorance": {{{_DIM}}}'
    "}"
)


@pytest.fixture
def observer(tmp_path: Path):
    cfg = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
    store = AuditStore(db_path=tmp_path / "audits.db")
    ollama = AsyncMock()
    ollama.list_models = AsyncMock(return_value=["qwen3:32b"])
    return ObserverAudit(config=cfg, ollama_client=ollama, audit_store=store)


class TestFailOpenPaths:
    async def test_timeout_fails_open(self, observer):
        async def _never(**kwargs):
            await asyncio.sleep(60)

        observer._ollama.chat = _never
        observer._config.observer = observer._config.observer.model_copy(
            update={"timeout_seconds": 1}
        )
        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert result.overall_passed is True
        assert result.error_type == "timeout"

    async def test_connection_error_fails_open(self, observer):
        observer._ollama.chat = AsyncMock(side_effect=ConnectionError("refused"))
        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert result.overall_passed is True

    async def test_malformed_json_fails_open(self, observer):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": "<<not json>>"}})
        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert result.overall_passed is True
        assert result.error_type == "parse_failed"

    async def test_empty_response_fails_open(self, observer):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": ""}})
        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert result.overall_passed is True

    async def test_all_dimensions_missing_fails_open(self, observer):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": "{}"}})
        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert result.overall_passed is True

    async def test_partial_audit_passes_with_skipped_markers(self, observer):
        partial = (
            '{"hallucination": {"passed": true, "reason": "",'
            ' "evidence": "", "fix_suggestion": ""}}'
        )
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": partial}})
        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert result.overall_passed is True
        assert result.dimensions["sycophancy"].reason.startswith("skipped")
        assert result.dimensions["laziness"].reason.startswith("skipped")
        assert result.dimensions["tool_ignorance"].reason.startswith("skipped")


class TestCircuitBreaker:
    async def test_opens_after_threshold_consecutive_failures(self, observer):
        observer._config.observer = observer._config.observer.model_copy(
            update={"circuit_breaker_threshold": 3, "timeout_seconds": 1}
        )

        async def _fail(**kwargs):
            raise ConnectionError("x")

        observer._ollama.chat = _fail

        for _ in range(3):
            await observer.audit(
                user_message="q",
                response="a",
                tool_results=[],
                session_id="s",
            )
        assert observer._circuit_open is True

        # Next call takes the short-circuit path (no LLM call at all).
        chat_mock = AsyncMock(return_value={"message": {"content": "x"}})
        observer._ollama.chat = chat_mock
        await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert chat_mock.called is False

    async def test_successful_call_resets_counter(self, observer):
        observer._config.observer = observer._config.observer.model_copy(
            update={"circuit_breaker_threshold": 3}
        )

        # Fail twice.
        observer._ollama.chat = AsyncMock(side_effect=ConnectionError("x"))
        for _ in range(2):
            await observer.audit(
                user_message="q",
                response="a",
                tool_results=[],
                session_id="s",
            )
        # Now succeed.
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": _ALL_PASS_JSON}})
        await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert observer._consecutive_failures == 0
        assert observer._circuit_open is False


class TestStoreFailures:
    async def test_store_write_failure_does_not_raise(self, observer, monkeypatch):
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": _ALL_PASS_JSON}})

        def _always_error(*args, **kwargs):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr("sqlite3.connect", _always_error)
        # Must NOT raise.
        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s",
        )
        assert result.overall_passed is True
