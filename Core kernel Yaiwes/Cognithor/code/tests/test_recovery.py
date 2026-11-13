"""Tests for failure taxonomy and recovery engine."""

from __future__ import annotations

from cognithor.core.recovery import (
    DEFAULT_RECIPES,
    EscalationPolicy,
    FailureClass,
    RecoveryEngine,
    RecoveryRecipe,
    RecoveryStep,
    classify_failure,
)

# ---------------------------------------------------------------------------
# classify_failure
# ---------------------------------------------------------------------------


class TestClassifyFailure:
    def test_timeout_error(self):
        assert classify_failure(TimeoutError("timed out")) == FailureClass.TOOL_TIMEOUT

    def test_connection_error(self):
        assert classify_failure(ConnectionError("refused")) == FailureClass.LLM_CONNECTION

    def test_connection_refused(self):
        assert classify_failure(ConnectionRefusedError()) == FailureClass.LLM_CONNECTION

    def test_permission_error(self):
        assert classify_failure(PermissionError("denied")) == FailureClass.GATEKEEPER_BLOCK

    def test_file_not_found(self):
        assert classify_failure(FileNotFoundError("missing")) == FailureClass.INFRA

    def test_memory_error(self):
        assert classify_failure(MemoryError()) == FailureClass.INFRA

    def test_rate_limit_keyword(self):
        """Keyword '429' in error message → rate limit."""
        exc = RuntimeError("HTTP 429 Too Many Requests")
        assert classify_failure(exc) == FailureClass.LLM_RATE_LIMIT

    def test_rate_limit_keyword_quota(self):
        exc = RuntimeError("Quota exceeded for model")
        assert classify_failure(exc) == FailureClass.LLM_RATE_LIMIT

    def test_gatekeeper_keyword(self):
        exc = RuntimeError("Action blocked by gatekeeper")
        assert classify_failure(exc) == FailureClass.GATEKEEPER_BLOCK

    def test_mcp_keyword(self):
        exc = RuntimeError("MCP handshake failed")
        assert classify_failure(exc) == FailureClass.MCP_ERROR

    def test_disk_keyword(self):
        exc = RuntimeError("No space left on disk")
        assert classify_failure(exc) == FailureClass.INFRA

    def test_unknown_defaults_to_tool_runtime(self):
        exc = ValueError("something weird")
        assert classify_failure(exc) == FailureClass.TOOL_RUNTIME

    def test_context_helps_classification(self):
        exc = RuntimeError("unknown error")
        assert classify_failure(exc, context="timeout during tool exec") == FailureClass.LLM_TIMEOUT


# ---------------------------------------------------------------------------
# DEFAULT_RECIPES
# ---------------------------------------------------------------------------


class TestDefaultRecipes:
    def test_all_failure_classes_have_recipes(self):
        for fc in FailureClass:
            assert fc in DEFAULT_RECIPES, f"Missing recipe for {fc}"

    def test_gatekeeper_escalates_immediately(self):
        recipe = DEFAULT_RECIPES[FailureClass.GATEKEEPER_BLOCK]
        assert recipe.steps == (RecoveryStep.ESCALATE_TO_USER,)
        assert recipe.max_attempts == 1

    def test_infra_aborts(self):
        recipe = DEFAULT_RECIPES[FailureClass.INFRA]
        assert recipe.escalation == EscalationPolicy.ABORT

    def test_tool_runtime_retries(self):
        recipe = DEFAULT_RECIPES[FailureClass.TOOL_RUNTIME]
        assert RecoveryStep.RETRY in recipe.steps
        assert recipe.max_attempts >= 1

    def test_llm_timeout_tries_provider_switch(self):
        recipe = DEFAULT_RECIPES[FailureClass.LLM_TIMEOUT]
        assert RecoveryStep.SWITCH_PROVIDER in recipe.steps


# ---------------------------------------------------------------------------
# RecoveryEngine
# ---------------------------------------------------------------------------


class TestRecoveryEngine:
    def test_classify(self):
        engine = RecoveryEngine()
        assert engine.classify(TimeoutError()) == FailureClass.TOOL_TIMEOUT

    def test_get_recipe(self):
        engine = RecoveryEngine()
        recipe = engine.get_recipe(FailureClass.TOOL_RUNTIME)
        assert recipe.failure_class == FailureClass.TOOL_RUNTIME

    def test_should_retry_first_attempt(self):
        engine = RecoveryEngine()
        assert engine.should_retry(FailureClass.TOOL_RUNTIME, "web_search", 1) is True

    def test_should_retry_exhausted(self):
        engine = RecoveryEngine()
        # Exhaust attempts
        for i in range(5):
            engine.should_retry(FailureClass.TOOL_RUNTIME, "web_search", i)
        assert engine.should_retry(FailureClass.TOOL_RUNTIME, "web_search", 10) is False

    def test_should_retry_gatekeeper_never(self):
        engine = RecoveryEngine()
        assert engine.should_retry(FailureClass.GATEKEEPER_BLOCK, "vault_delete", 1) is False

    def test_record_recovery(self):
        engine = RecoveryEngine()
        event = engine.record_recovery(
            FailureClass.TOOL_RUNTIME, RecoveryStep.RETRY, attempt=1, success=True
        )
        assert event.success is True
        assert event.failure_class == FailureClass.TOOL_RUNTIME

    def test_build_result_recovered(self):
        engine = RecoveryEngine()
        result = engine.build_result(FailureClass.TOOL_RUNTIME, recovered=True, events=[])
        assert result.recovered is True
        assert result.escalation is None

    def test_build_result_not_recovered(self):
        engine = RecoveryEngine()
        result = engine.build_result(
            FailureClass.INFRA, recovered=False, events=[], original_error="disk full"
        )
        assert result.recovered is False
        assert result.escalation == EscalationPolicy.ABORT
        assert result.original_error == "disk full"

    def test_reset_tool(self):
        engine = RecoveryEngine()
        engine.should_retry(FailureClass.TOOL_RUNTIME, "web_search", 1)
        assert engine.stats()["active_counters"] > 0
        engine.reset("web_search")
        assert engine.stats()["active_counters"] == 0

    def test_reset_all(self):
        engine = RecoveryEngine()
        engine.should_retry(FailureClass.TOOL_RUNTIME, "web_search", 1)
        engine.should_retry(FailureClass.LLM_TIMEOUT, "planner", 1)
        engine.reset()
        assert engine.stats()["active_counters"] == 0

    def test_custom_recipes(self):
        custom = {
            FailureClass.TOOL_RUNTIME: RecoveryRecipe(
                failure_class=FailureClass.TOOL_RUNTIME,
                steps=(RecoveryStep.CLEAR_CACHE,),
                max_attempts=5,
            ),
        }
        engine = RecoveryEngine(recipes=custom)
        recipe = engine.get_recipe(FailureClass.TOOL_RUNTIME)
        assert recipe.max_attempts == 5
        assert recipe.steps == (RecoveryStep.CLEAR_CACHE,)

    def test_stats(self):
        engine = RecoveryEngine()
        stats = engine.stats()
        assert stats["recipes"] == 8
        assert stats["active_counters"] == 0
