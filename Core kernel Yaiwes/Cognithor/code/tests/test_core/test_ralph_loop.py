"""Tests for the Ralph Agent-Loop (iterative multi-step autonomous execution)."""

from __future__ import annotations

import asyncio

import pytest

from cognithor.core.ralph_loop import (
    RALPH_PROMPT_FRAGMENT,
    RalphConfig,
    RalphLoop,
    RalphResult,
    RalphSignal,
    parse_signal,
    run_ralph_loop,
)

# ============================================================================
# Helpers
# ============================================================================


class FakePGERunner:
    """Configurable fake PGE runner for testing."""

    def __init__(
        self,
        responses: list[tuple[str, list[str]]] | None = None,
        delay: float = 0.0,
    ) -> None:
        self.responses = responses or []
        self.delay = delay
        self.call_count = 0
        self.inputs: list[str] = []
        self.ralph_prompts: list[str] = []

    async def __call__(
        self,
        user_input: str,
        *,
        ralph_prompt: str,
    ) -> tuple[str, list[str]]:
        self.inputs.append(user_input)
        self.ralph_prompts.append(ralph_prompt)
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        idx = min(self.call_count, len(self.responses) - 1)
        self.call_count += 1
        return self.responses[idx]


class ErrorPGERunner:
    """PGE runner that raises on the Nth call."""

    def __init__(self, fail_on: int = 0, error: type = RuntimeError) -> None:
        self.fail_on = fail_on
        self.call_count = 0
        self.error = error

    async def __call__(
        self,
        user_input: str,
        *,
        ralph_prompt: str,
    ) -> tuple[str, list[str]]:
        if self.call_count == self.fail_on:
            self.call_count += 1
            raise self.error("PGE failed")
        self.call_count += 1
        return "[STOP: done]", ["tool_a"]


class TimeoutPGERunner:
    """PGE runner that raises TimeoutError."""

    async def __call__(
        self,
        user_input: str,
        *,
        ralph_prompt: str,
    ) -> tuple[str, list[str]]:
        raise TimeoutError("iteration timed out")


# ============================================================================
# Signal parsing tests
# ============================================================================


class TestParseSignal:
    def test_continue_bracket(self) -> None:
        text = "I did step 1. [CONTINUE: now do step 2]"
        signal, detail = parse_signal(text)
        assert signal == RalphSignal.CONTINUE
        assert detail == "now do step 2"

    def test_stop_bracket(self) -> None:
        text = "All done. [STOP: created 3 files and ran tests]"
        signal, detail = parse_signal(text)
        assert signal == RalphSignal.STOP
        assert detail == "created 3 files and ran tests"

    def test_no_signal(self) -> None:
        text = "Here is some regular output without any signal."
        signal, detail = parse_signal(text)
        assert signal == RalphSignal.NONE
        assert detail == ""

    def test_continue_json_style(self) -> None:
        text = '{"action": "continue", "next_step": "install dependencies"}'
        signal, detail = parse_signal(text)
        assert signal == RalphSignal.CONTINUE
        assert detail == "install dependencies"

    def test_continue_case_insensitive(self) -> None:
        text = "[continue: check results]"
        signal, detail = parse_signal(text)
        assert signal == RalphSignal.CONTINUE
        assert detail == "check results"

    def test_stop_takes_priority_when_both_present(self) -> None:
        text = "[CONTINUE: more work] [STOP: actually done]"
        signal, detail = parse_signal(text)
        assert signal == RalphSignal.STOP
        assert detail == "actually done"

    def test_json_continue_without_next_step(self) -> None:
        text = '{"action": "continue"}'
        signal, detail = parse_signal(text)
        assert signal == RalphSignal.CONTINUE
        assert detail == ""


# ============================================================================
# Max iterations cap
# ============================================================================


class TestMaxIterations:
    @pytest.mark.asyncio
    async def test_stops_at_max_iterations(self) -> None:
        responses = [
            ("[CONTINUE: step N]", ["tool_a", "tool_b"]),
        ]
        runner = FakePGERunner(responses=responses)
        config = RalphConfig(max_iterations=3, require_progress=False)
        loop = RalphLoop(config=config)

        result = await loop.run("do stuff", runner)

        assert len(result.iterations) == 3
        assert result.stop_reason == "max_iterations"
        assert not result.converged
        assert runner.call_count == 3

    @pytest.mark.asyncio
    async def test_default_max_is_10(self) -> None:
        config = RalphConfig()
        assert config.max_iterations == 10


# ============================================================================
# CONTINUE signal handling
# ============================================================================


class TestContinueSignal:
    @pytest.mark.asyncio
    async def test_feeds_next_step_as_input(self) -> None:
        responses = [
            ("[CONTINUE: do step 2]", ["search"]),
            ("[STOP: all done]", ["write"]),
        ]
        runner = FakePGERunner(responses=responses)
        config = RalphConfig(max_iterations=5)
        loop = RalphLoop(config=config)

        result = await loop.run("start task", runner)

        assert runner.call_count == 2
        assert runner.inputs[0] == "start task"
        assert runner.inputs[1] == "do step 2"
        assert result.converged
        assert result.stop_reason == "completed"

    @pytest.mark.asyncio
    async def test_ralph_prompt_passed_to_runner(self) -> None:
        runner = FakePGERunner(responses=[("[STOP: done]", [])])
        loop = RalphLoop()

        await loop.run("task", runner)

        assert runner.ralph_prompts[0] == RALPH_PROMPT_FRAGMENT


# ============================================================================
# STOP signal handling
# ============================================================================


class TestStopSignal:
    @pytest.mark.asyncio
    async def test_stops_on_stop_signal(self) -> None:
        responses = [
            ("[CONTINUE: step 2]", ["tool_a"]),
            ("[STOP: completed the analysis]", ["tool_b"]),
        ]
        runner = FakePGERunner(responses=responses)
        loop = RalphLoop(config=RalphConfig(require_progress=False))

        result = await loop.run("analyze X", runner)

        assert len(result.iterations) == 2
        assert result.converged
        assert result.stop_reason == "completed"

    @pytest.mark.asyncio
    async def test_no_signal_implicit_stop(self) -> None:
        responses = [
            ("Here is the answer without any signal.", ["tool_a"]),
        ]
        runner = FakePGERunner(responses=responses)
        loop = RalphLoop()

        result = await loop.run("question", runner)

        assert len(result.iterations) == 1
        assert result.stop_reason == "no_signal"
        assert not result.converged


# ============================================================================
# Progress detection
# ============================================================================


class TestProgressDetection:
    @pytest.mark.asyncio
    async def test_identical_iterations_force_stop(self) -> None:
        """Two consecutive iterations with identical tool calls -> stop."""
        responses = [
            ("[CONTINUE: retry]", ["web_search", "read_file"]),
        ]
        runner = FakePGERunner(responses=responses)
        config = RalphConfig(max_iterations=10, require_progress=True)
        loop = RalphLoop(config=config)

        result = await loop.run("find X", runner)

        assert result.stop_reason == "no_progress"
        assert len(result.iterations) == 2  # stopped after 2 identical

    @pytest.mark.asyncio
    async def test_progress_detection_disabled(self) -> None:
        """With require_progress=False, identical iterations don't stop."""
        responses = [
            ("[CONTINUE: retry]", ["web_search"]),
        ]
        runner = FakePGERunner(responses=responses)
        config = RalphConfig(max_iterations=3, require_progress=False)
        loop = RalphLoop(config=config)

        result = await loop.run("find X", runner)

        assert result.stop_reason == "max_iterations"
        assert len(result.iterations) == 3

    @pytest.mark.asyncio
    async def test_different_tools_allow_progress(self) -> None:
        responses = [
            ("[CONTINUE: step 2]", ["web_search"]),
            ("[CONTINUE: step 3]", ["read_file"]),
            ("[STOP: done]", ["write_file"]),
        ]
        runner = FakePGERunner(responses=responses)
        config = RalphConfig(max_iterations=10, require_progress=True)
        loop = RalphLoop(config=config)

        result = await loop.run("do X", runner)

        assert result.converged
        assert len(result.iterations) == 3


# ============================================================================
# Budget / timeout
# ============================================================================


class TestBudgetTimeout:
    @pytest.mark.asyncio
    async def test_total_budget_exceeded(self) -> None:
        """Loop stops when total budget is exceeded."""
        responses = [
            ("[CONTINUE: more]", ["tool_a"]),
        ]
        runner = FakePGERunner(responses=responses, delay=0.05)
        config = RalphConfig(
            max_iterations=100,
            total_budget_seconds=0.08,
            require_progress=False,
        )
        loop = RalphLoop(config=config)

        result = await loop.run("long task", runner)

        assert result.stop_reason == "total_budget_exceeded"
        assert result.total_duration_seconds > 0

    @pytest.mark.asyncio
    async def test_iteration_timeout_stops_loop(self) -> None:
        runner = TimeoutPGERunner()
        loop = RalphLoop()

        result = await loop.run("task", runner)

        assert result.stop_reason == "iteration_timeout"
        assert len(result.iterations) == 0


# ============================================================================
# Iteration history tracking
# ============================================================================


class TestIterationHistory:
    @pytest.mark.asyncio
    async def test_records_all_iterations(self) -> None:
        responses = [
            ("[CONTINUE: step 2]", ["search", "read"]),
            ("[CONTINUE: step 3]", ["write"]),
            ("[STOP: finished]", ["verify"]),
        ]
        runner = FakePGERunner(responses=responses)
        loop = RalphLoop(config=RalphConfig(require_progress=False))

        result = await loop.run("big task", runner)

        assert len(result.iterations) == 3
        # First iteration
        assert result.iterations[0].iteration == 0
        assert result.iterations[0].tools_called == ["search", "read"]
        assert result.iterations[0].signal == RalphSignal.CONTINUE
        assert result.iterations[0].next_step == "step 2"
        # Second
        assert result.iterations[1].tools_called == ["write"]
        assert result.iterations[1].signal == RalphSignal.CONTINUE
        # Third
        assert result.iterations[2].tools_called == ["verify"]
        assert result.iterations[2].signal == RalphSignal.STOP
        assert result.iterations[2].next_step == ""

    @pytest.mark.asyncio
    async def test_output_summary_truncated(self) -> None:
        long_text = "A" * 500 + " [STOP: done]"
        runner = FakePGERunner(responses=[(long_text, [])])
        loop = RalphLoop()

        result = await loop.run("task", runner)

        assert len(result.iterations[0].output_summary) == 200

    @pytest.mark.asyncio
    async def test_duration_tracked(self) -> None:
        runner = FakePGERunner(responses=[("[STOP: done]", [])], delay=0.01)
        loop = RalphLoop()

        result = await loop.run("task", runner)

        assert result.iterations[0].duration_seconds >= 0.0
        assert result.total_duration_seconds >= 0.0


# ============================================================================
# Cancellation
# ============================================================================


class TestCancellation:
    @pytest.mark.asyncio
    async def test_cancel_stops_loop(self) -> None:
        responses = [
            ("[CONTINUE: more]", ["tool"]),
        ]
        runner = FakePGERunner(responses=responses)
        loop = RalphLoop(config=RalphConfig(max_iterations=100, require_progress=False))

        # Cancel before first iteration
        loop.cancel()
        result = await loop.run("task", runner)

        assert result.stop_reason == "cancelled"
        assert len(result.iterations) == 0


# ============================================================================
# Error handling
# ============================================================================


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_pge_error_stops_loop(self) -> None:
        runner = ErrorPGERunner(fail_on=0)
        loop = RalphLoop()

        result = await loop.run("task", runner)

        assert result.stop_reason == "error"
        assert len(result.iterations) == 0

    @pytest.mark.asyncio
    async def test_error_after_successful_iteration(self) -> None:
        """Error on 2nd call, first succeeded."""
        call_count = 0

        async def mixed_runner(user_input: str, *, ralph_prompt: str) -> tuple[str, list[str]]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "[CONTINUE: step 2]", ["tool_a"]
            raise RuntimeError("boom")

        loop = RalphLoop(config=RalphConfig(require_progress=False))
        result = await loop.run("task", mixed_runner)

        assert result.stop_reason == "error"
        assert len(result.iterations) == 1
        assert result.iterations[0].signal == RalphSignal.CONTINUE


# ============================================================================
# Convenience function
# ============================================================================


class TestRunRalphLoop:
    @pytest.mark.asyncio
    async def test_convenience_function(self) -> None:
        runner = FakePGERunner(responses=[("[STOP: done]", ["tool"])])
        result = await run_ralph_loop("task", runner)

        assert isinstance(result, RalphResult)
        assert result.converged
        assert result.stop_reason == "completed"

    @pytest.mark.asyncio
    async def test_convenience_with_config(self) -> None:
        runner = FakePGERunner(responses=[("[STOP: ok]", [])])
        config = RalphConfig(max_iterations=5)
        result = await run_ralph_loop("task", runner, config=config)

        assert result.converged


# ============================================================================
# Prompt fragment
# ============================================================================


class TestPromptFragment:
    def test_contains_continue_instruction(self) -> None:
        assert "[CONTINUE:" in RALPH_PROMPT_FRAGMENT

    def test_contains_stop_instruction(self) -> None:
        assert "[STOP:" in RALPH_PROMPT_FRAGMENT
