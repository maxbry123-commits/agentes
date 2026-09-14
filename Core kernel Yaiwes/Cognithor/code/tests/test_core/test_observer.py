"""Unit tests for the Observer audit layer."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock

import pytest

from cognithor.core.observer import (
    AuditResult,
    DimensionResult,
    PGEReloopDirective,
    ResponseEnvelope,
)
from cognithor.models import ToolResult


@pytest.fixture
def observer(tmp_path):
    """ObserverAudit with default config and tmp_path audit store."""
    from cognithor.config import CognithorConfig
    from cognithor.core.observer import ObserverAudit
    from cognithor.core.observer_store import AuditStore

    config = CognithorConfig()
    store = AuditStore(db_path=tmp_path / "audits.db")
    return ObserverAudit(config=config, ollama_client=None, audit_store=store)


class TestDataclasses:
    def test_dimension_result_basic(self):
        r = DimensionResult(
            name="hallucination",
            passed=False,
            reason="Claim not in tool results",
            evidence="'TechCorp founded 2015'",
            fix_suggestion="Remove unsupported claim",
        )
        assert r.name == "hallucination"
        assert r.passed is False
        # Frozen dataclass
        with pytest.raises(FrozenInstanceError):
            r.passed = True  # type: ignore[misc]

    def test_audit_result_pass_path(self):
        dim_pass = DimensionResult(
            name="hallucination", passed=True, reason="", evidence="", fix_suggestion=""
        )
        r = AuditResult(
            overall_passed=True,
            dimensions={"hallucination": dim_pass},
            retry_count=0,
            final_action="pass",
            retry_strategy="deliver",
            model="qwen3:32b",
            duration_ms=3200,
            degraded_mode=False,
            error_type=None,
        )
        assert r.overall_passed is True
        assert r.final_action == "pass"

    def test_pge_reloop_directive(self):
        d = PGEReloopDirective(
            reason="tool_ignorance",
            missing_data="current weather data",
            suggested_tools=["web_search", "api_call"],
        )
        assert d.reason == "tool_ignorance"
        assert "web_search" in d.suggested_tools

    def test_response_envelope_delivers(self):
        e = ResponseEnvelope(content="Hello", directive=None)
        assert e.content == "Hello"
        assert e.directive is None

    def test_response_envelope_with_directive(self):
        d = PGEReloopDirective(reason="tool_ignorance", missing_data="...", suggested_tools=[])
        e = ResponseEnvelope(content="draft", directive=d)
        assert e.directive is not None
        assert e.directive.reason == "tool_ignorance"


class TestBuildPrompt:
    def test_includes_all_four_dimensions(self, observer):
        messages = observer._build_prompt(
            user_message="What's 2+2?",
            response="The answer is 4.",
            tool_results=[],
        )
        system_msg = messages[0]["content"]
        for dim in ("hallucination", "sycophancy", "laziness", "tool_ignorance"):
            assert dim in system_msg.lower()

    def test_embeds_user_message_and_response(self, observer):
        messages = observer._build_prompt(
            user_message="FOO_USER_MSG",
            response="BAR_RESPONSE",
            tool_results=[],
        )
        user_payload = messages[1]["content"]
        assert "FOO_USER_MSG" in user_payload
        assert "BAR_RESPONSE" in user_payload

    def test_embeds_tool_results(self, observer):
        tool_result = ToolResult(
            tool_name="web_search",
            content="TechCorp was founded in 2015",
            is_error=False,
        )
        messages = observer._build_prompt(
            user_message="When was TechCorp founded?",
            response="TechCorp was founded in 2015.",
            tool_results=[tool_result],
        )
        user_payload = messages[1]["content"]
        assert "web_search" in user_payload
        assert "TechCorp was founded in 2015" in user_payload

    def test_renders_tool_error(self, observer):
        result = ToolResult(
            tool_name="api_call",
            content="",
            is_error=True,
            error_message="timeout",
        )
        messages = observer._build_prompt(user_message="Q", response="A", tool_results=[result])
        assert "ERROR: timeout" in messages[1]["content"]

    def test_renders_tool_error_without_message(self, observer):
        result = ToolResult(
            tool_name="api_call",
            content="",
            is_error=True,
            error_message=None,
        )
        messages = observer._build_prompt(user_message="Q", response="A", tool_results=[result])
        # Must NOT contain the literal string "None" — use a sentinel instead.
        assert "ERROR: None" not in messages[1]["content"]
        assert "ERROR: (no error message)" in messages[1]["content"]


class TestCallLlmAudit:
    async def test_returns_raw_text_on_success(self, observer):
        _audit_json = (
            '{"hallucination": {"passed": true, "reason": "",'
            ' "evidence": "", "fix_suggestion": ""}}'
        )
        observer._ollama = AsyncMock()
        observer._ollama.chat = AsyncMock(
            return_value={
                "message": {"content": _audit_json},
            }
        )
        text = await observer._call_llm_audit(
            messages=[{"role": "system", "content": "x"}],
        )
        assert text.startswith("{")

    async def test_timeout_returns_none(self, observer, monkeypatch):
        import asyncio

        async def _slow_chat(**kwargs):
            await asyncio.sleep(10)
            return {"message": {"content": "x"}}

        observer._ollama = AsyncMock()
        observer._ollama.chat = _slow_chat

        # Override timeout to 1s
        observer._config.observer = observer._config.observer.model_copy(
            update={"timeout_seconds": 1}
        )

        result = await observer._call_llm_audit(
            messages=[{"role": "system", "content": "x"}],
        )
        # Must return None on timeout (fail-open signal)
        assert result is None


class TestParseResponse:
    def test_parses_valid_four_dimensions(self, observer):
        raw = (
            '{"hallucination": {"passed": true, "reason": "all claims match tools",'
            ' "evidence": "", "fix_suggestion": ""},'
            ' "sycophancy": {"passed": true, "reason": "neutral tone",'
            ' "evidence": "", "fix_suggestion": ""},'
            ' "laziness": {"passed": true, "reason": "concrete answer",'
            ' "evidence": "", "fix_suggestion": ""},'
            ' "tool_ignorance": {"passed": true, "reason": "appropriate tool use",'
            ' "evidence": "", "fix_suggestion": ""}}'
        )
        dims = observer._parse_response(raw)
        assert dims is not None
        assert set(dims.keys()) == {"hallucination", "sycophancy", "laziness", "tool_ignorance"}
        assert all(d.passed for d in dims.values())

    def test_invalid_json_returns_none(self, observer):
        assert observer._parse_response("this is not json") is None

    def test_missing_dimension_produces_partial(self, observer):
        raw = (
            '{"hallucination": {"passed": false, "reason": "made up date",'
            ' "evidence": "2015", "fix_suggestion": "remove"},'
            ' "sycophancy": {"passed": true, "reason": "",'
            ' "evidence": "", "fix_suggestion": ""}}'
        )
        dims = observer._parse_response(raw)
        assert dims is not None
        assert dims["hallucination"].passed is False
        assert dims["sycophancy"].passed is True
        # Missing dimensions → treated as "skipped" = passed
        assert dims["laziness"].passed is True
        assert dims["laziness"].reason == "skipped (missing from LLM response)"
        assert dims["tool_ignorance"].passed is True

    def test_all_dimensions_missing_returns_none(self, observer):
        assert observer._parse_response("{}") is None

    def test_dict_without_passed_key_treated_as_skipped(self, observer):
        # LLM returns a dict entry but omits the 'passed' field — must be
        # treated as skipped=passed, same as a missing dimension.
        raw = (
            '{"hallucination": {"reason": "claims unsupported"},'
            ' "sycophancy": {"passed": true, "reason": "", "evidence": "",'
            ' "fix_suggestion": ""}}'
        )
        dims = observer._parse_response(raw)
        assert dims is not None
        assert dims["hallucination"].passed is True
        assert dims["hallucination"].reason == "skipped (missing from LLM response)"
        # sycophancy still parses normally from the well-formed dict
        assert dims["sycophancy"].passed is True


def _dim(name: str, passed: bool) -> DimensionResult:
    return DimensionResult(
        name=name,  # type: ignore[arg-type]
        passed=passed,
        reason="" if passed else "bad",
        evidence="" if passed else "x",
        fix_suggestion="" if passed else "fix",
    )


class TestDecideRetryStrategy:
    def test_all_pass_returns_deliver(self, observer):
        dims = {
            "hallucination": _dim("hallucination", True),
            "sycophancy": _dim("sycophancy", True),
            "laziness": _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        assert overall is True
        assert strategy == "deliver"

    def test_only_advisory_fail_still_delivers(self, observer):
        dims = {
            "hallucination": _dim("hallucination", True),
            "sycophancy": _dim("sycophancy", False),
            "laziness": _dim("laziness", False),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        assert overall is True
        assert strategy == "deliver"

    def test_hallucination_fail_triggers_response_regen(self, observer):
        dims = {
            "hallucination": _dim("hallucination", False),
            "sycophancy": _dim("sycophancy", True),
            "laziness": _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        assert overall is False
        assert strategy == "response_regen"

    def test_tool_ignorance_fail_triggers_pge_reloop(self, observer):
        dims = {
            "hallucination": _dim("hallucination", True),
            "sycophancy": _dim("sycophancy", True),
            "laziness": _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", False),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        assert overall is False
        assert strategy == "pge_reloop"

    def test_both_blocking_fail_tool_ignorance_wins(self, observer):
        dims = {
            "hallucination": _dim("hallucination", False),
            "sycophancy": _dim("sycophancy", True),
            "laziness": _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", False),
        }
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=0)
        # Tool-ignorance fix is more fundamental (new data via new tool call)
        # than response regen — priority: pge_reloop wins.
        assert overall is False
        assert strategy == "pge_reloop"

    def test_retries_exhausted_switches_to_warning(self, observer):
        dims = {
            "hallucination": _dim("hallucination", False),
            "sycophancy": _dim("sycophancy", True),
            "laziness": _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        # max_retries is 2 by default; retry_count=2 means we've already retried twice
        overall, strategy = observer._decide_retry_strategy(dims, retry_count=2)
        assert overall is False
        assert strategy == "deliver_with_warning"


def _all_pass_json() -> str:
    """JSON string with all four dimensions passing — shared by multiple tests."""
    dim = '"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""'
    return (
        "{"
        f'"hallucination": {{{dim}}},'
        f'"sycophancy": {{{dim}}},'
        f'"laziness": {{{dim}}},'
        f'"tool_ignorance": {{{dim}}}'
        "}"
    )


class TestAuditMain:
    async def test_pass_path(self, observer):
        observer._ollama = AsyncMock()
        observer._ollama.list_models = AsyncMock(return_value=["qwen3:32b"])
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": _all_pass_json()}})
        result = await observer.audit(
            user_message="hi",
            response="hello",
            tool_results=[],
            session_id="s1",
            retry_count=0,
        )
        assert result.overall_passed is True
        assert result.final_action == "pass"
        assert result.retry_strategy == "deliver"
        assert result.model == "qwen3:32b"
        assert result.degraded_mode is False
        assert result.duration_ms >= 0

    async def test_hallucination_rejection(self, observer):
        dim_pass = '"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""'
        dim_fail = (
            '"passed": false, "reason": "unsupported date",'
            ' "evidence": "2015", "fix_suggestion": "remove"'
        )
        audit_json = (
            "{"
            f'"hallucination": {{{dim_fail}}},'
            f'"sycophancy": {{{dim_pass}}},'
            f'"laziness": {{{dim_pass}}},'
            f'"tool_ignorance": {{{dim_pass}}}'
            "}"
        )
        observer._ollama = AsyncMock()
        observer._ollama.list_models = AsyncMock(return_value=["qwen3:32b"])
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": audit_json}})
        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s2",
            retry_count=0,
        )
        assert result.overall_passed is False
        assert result.final_action == "rejected_with_retry"
        assert result.retry_strategy == "response_regen"

    async def test_fail_open_on_timeout(self, observer):
        import asyncio

        async def _slow(**kwargs):
            await asyncio.sleep(5)
            return {"message": {"content": "x"}}

        observer._ollama = AsyncMock()
        observer._ollama.list_models = AsyncMock(return_value=["qwen3:32b"])
        observer._ollama.chat = _slow
        observer._config.observer = observer._config.observer.model_copy(
            update={"timeout_seconds": 1}
        )

        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s3",
            retry_count=0,
        )
        assert result.overall_passed is True  # fail-open
        assert result.error_type == "timeout"

    async def test_records_to_store(self, observer):
        observer._ollama = AsyncMock()
        observer._ollama.list_models = AsyncMock(return_value=["qwen3:32b"])
        observer._ollama.chat = AsyncMock(return_value={"message": {"content": _all_pass_json()}})
        await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s4",
            retry_count=0,
        )
        import sqlite3

        with sqlite3.connect(observer._store._db_path) as conn:
            rows = conn.execute("SELECT session_id FROM audits").fetchall()
        assert rows == [("s4",)]


class TestBuildRetryFeedback:
    def test_feedback_is_structured_json(self, observer):
        dims = {
            "hallucination": _dim("hallucination", False),
            "sycophancy": _dim("sycophancy", True),
            "laziness": _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        result = AuditResult(
            overall_passed=False,
            dimensions=dims,
            retry_count=0,
            final_action="rejected_with_retry",
            retry_strategy="response_regen",
            model="qwen3:32b",
            duration_ms=100,
            degraded_mode=False,
            error_type=None,
        )
        fb = observer.build_retry_feedback(result)
        assert fb["role"] == "system"

        import json as _json

        payload = _json.loads(fb["content"])
        assert "observer_rejection" in payload
        rejection = payload["observer_rejection"]
        assert rejection["dimensions_failed"] == ["hallucination"]
        assert rejection["retry_count"] == 0
        assert rejection["max_retries"] == 2
        assert len(rejection["reasons"]) == 1
        assert len(rejection["fix_suggestions"]) == 1


class TestBuildPgeDirective:
    def test_directive_includes_missing_data_and_suggestions(self, observer):
        dim = DimensionResult(
            name="tool_ignorance",
            passed=False,
            reason="Question required web research but no tool was called",
            evidence="I don't have current data on that",
            fix_suggestion="Call web_search to get current data",
        )
        dims = {
            "hallucination": _dim("hallucination", True),
            "sycophancy": _dim("sycophancy", True),
            "laziness": _dim("laziness", True),
            "tool_ignorance": dim,
        }
        result = AuditResult(
            overall_passed=False,
            dimensions=dims,
            retry_count=0,
            final_action="rejected_with_retry",
            retry_strategy="pge_reloop",
            model="qwen3:32b",
            duration_ms=100,
            degraded_mode=False,
            error_type=None,
        )
        directive = observer.build_pge_directive(result)
        assert directive is not None
        assert directive.reason == "tool_ignorance"
        assert "web research" in directive.missing_data
        assert "web_search" in directive.suggested_tools

    def test_returns_none_when_no_tool_ignorance(self, observer):
        dims = {
            "hallucination": _dim("hallucination", False),
            "sycophancy": _dim("sycophancy", True),
            "laziness": _dim("laziness", True),
            "tool_ignorance": _dim("tool_ignorance", True),
        }
        result = AuditResult(
            overall_passed=False,
            dimensions=dims,
            retry_count=0,
            final_action="rejected_with_retry",
            retry_strategy="response_regen",
            model="qwen3:32b",
            duration_ms=100,
            degraded_mode=False,
            error_type=None,
        )
        assert observer.build_pge_directive(result) is None


class TestDegradedMode:
    async def test_observer_model_missing_falls_back_to_planner(self, observer):
        # OllamaClient.list_models() indicates observer model missing, planner available.
        observer._ollama = AsyncMock()
        observer._ollama.list_models = AsyncMock(return_value=["qwen3:32b"])
        # Audit itself succeeds.
        _dim_json = '"passed": true, "reason": "", "evidence": "", "fix_suggestion": ""'
        observer._ollama.chat = AsyncMock(
            return_value={
                "message": {
                    "content": (
                        "{"
                        f'"hallucination":  {{{_dim_json}}},'
                        f'"sycophancy":     {{{_dim_json}}},'
                        f'"laziness":       {{{_dim_json}}},'
                        f'"tool_ignorance": {{{_dim_json}}}'
                        "}"
                    )
                }
            }
        )
        # Override observer model to an unavailable one.
        from cognithor.models import ModelConfig

        observer._config.models = observer._config.models.model_copy(
            update={"observer": ModelConfig(name="nonexistent-model:99b")}
        )

        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s1",
        )
        assert result.degraded_mode is True
        # Actual model used = planner model (qwen3:32b) since observer model was missing.
        assert result.model == "qwen3:32b"

    async def test_both_models_missing_returns_model_unavailable(self, observer):
        # list_models returns empty — neither observer nor planner available.
        observer._ollama = AsyncMock()
        observer._ollama.list_models = AsyncMock(return_value=[])

        result = await observer.audit(
            user_message="q",
            response="a",
            tool_results=[],
            session_id="s1",
        )
        assert result.overall_passed is True  # fail-open
        assert result.error_type == "model_unavailable"


class TestFixtureLibrary:
    def test_case_library_has_required_coverage(self):
        from tests.fixtures.observer_cases import ALL_CASES

        by_category = {
            "hallucination": 0,
            "sycophancy": 0,
            "laziness": 0,
            "tool_ignorance": 0,
            "clean": 0,
        }
        for case in ALL_CASES:
            by_category[case.category] += 1
        # Minimum counts per spec §Testing 5.4
        assert by_category["hallucination"] >= 20
        assert by_category["sycophancy"] >= 15
        assert by_category["laziness"] >= 15
        assert by_category["tool_ignorance"] >= 15
        assert by_category["clean"] >= 20
