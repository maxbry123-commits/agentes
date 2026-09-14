"""Ralph Agent-Loop -- iterative multi-step autonomous task execution.

Wraps the existing PGE cycle (Plan -> Gate -> Execute) and enables the
Planner to request continuation via CONTINUE/STOP signals, allowing
Jarvis to autonomously complete multi-step tasks.

The loop:
  1. Runs a PGE cycle
  2. Inspects the Planner response for [CONTINUE: ...] or [STOP: ...]
  3. If CONTINUE: feeds next_step back as input for another PGE cycle
  4. If STOP or no signal or budget exceeded: breaks and returns results

Safety caps: max iterations, per-iteration timeout, total timeout,
and progress detection (reuses ToolLoopDetector).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# ============================================================================
# Constants
# ============================================================================

DEFAULT_MAX_ITERATIONS = 10
DEFAULT_ITERATION_BUDGET = 300.0  # 5 min per iteration
DEFAULT_TOTAL_BUDGET = 1800.0  # 30 min total
IDENTICAL_ITERATION_THRESHOLD = 2  # stop after N identical iterations

# Signal patterns in Planner output
_CONTINUE_RE = re.compile(
    r"\[CONTINUE:\s*(?P<reason>[^\]]+)\]",
    re.IGNORECASE,
)
_STOP_RE = re.compile(
    r"\[STOP:\s*(?P<summary>[^\]]+)\]",
    re.IGNORECASE,
)
_JSON_CONTINUE_RE = re.compile(
    r'"action"\s*:\s*"continue"',
    re.IGNORECASE,
)
_JSON_NEXT_STEP_RE = re.compile(
    r'"next_step"\s*:\s*"(?P<next_step>[^"]+)"',
    re.IGNORECASE,
)

# ============================================================================
# Prompt fragment
# ============================================================================

RALPH_PROMPT_FRAGMENT = """\

You are in autonomous multi-step mode (Ralph Loop). After completing each step:
- If more steps are needed: respond with [CONTINUE: description of next step]
- If the task is complete: respond with [STOP: summary of what was accomplished]
Do NOT proceed without signaling. Always include exactly one signal at the end of your response."""


# ============================================================================
# Data models
# ============================================================================


class RalphSignal(StrEnum):
    """Signal parsed from Planner output."""

    CONTINUE = "continue"
    STOP = "stop"
    NONE = "none"


@dataclass
class IterationRecord:
    """Record of a single Ralph Loop iteration."""

    iteration: int
    tools_called: list[str]
    output_summary: str
    duration_seconds: float
    signal: RalphSignal
    next_step: str = ""


@dataclass
class RalphResult:
    """Final result of a Ralph Loop run."""

    final_response: str
    iterations: list[IterationRecord]
    total_duration_seconds: float
    stop_reason: str
    converged: bool  # True if stopped via STOP signal (task complete)


@dataclass
class RalphConfig:
    """Configuration for a Ralph Loop run."""

    max_iterations: int = DEFAULT_MAX_ITERATIONS
    iteration_budget_seconds: float = DEFAULT_ITERATION_BUDGET
    total_budget_seconds: float = DEFAULT_TOTAL_BUDGET
    require_progress: bool = True


# ============================================================================
# PGE Cycle protocol -- what the Gateway must provide
# ============================================================================


class PGECycleRunner(Protocol):
    """Protocol for running a single PGE cycle.

    The Gateway (or a test stub) must implement this interface.
    Returns (response_text, tools_called_names).
    """

    async def __call__(
        self,
        user_input: str,
        *,
        ralph_prompt: str,
    ) -> tuple[str, list[str]]: ...


# ============================================================================
# Signal parsing
# ============================================================================


def parse_signal(text: str) -> tuple[RalphSignal, str]:
    """Parse CONTINUE/STOP signal from Planner output.

    Returns:
        (signal_type, detail) where detail is the reason/summary/next_step.
    """
    # Check bracket-style STOP first (takes priority)
    m = _STOP_RE.search(text)
    if m:
        return RalphSignal.STOP, m.group("summary").strip()

    # Check bracket-style CONTINUE
    m = _CONTINUE_RE.search(text)
    if m:
        return RalphSignal.CONTINUE, m.group("reason").strip()

    # Check JSON-style continue
    if _JSON_CONTINUE_RE.search(text):
        m2 = _JSON_NEXT_STEP_RE.search(text)
        next_step = m2.group("next_step").strip() if m2 else ""
        return RalphSignal.CONTINUE, next_step

    return RalphSignal.NONE, ""


def _tools_signature(tools: list[str]) -> str:
    """Create a comparable signature from a tools list."""
    return ",".join(sorted(tools))


# ============================================================================
# Ralph Loop
# ============================================================================


class RalphLoop:
    """Iterative multi-step autonomous loop wrapping PGE cycles.

    Usage::

        loop = RalphLoop(config=RalphConfig(max_iterations=5))
        result = await loop.run(
            initial_input="Research and summarize X",
            pge_runner=my_pge_runner,
        )
        print(result.final_response)
        print(f"Completed in {len(result.iterations)} iterations")
    """

    def __init__(self, config: RalphConfig | None = None) -> None:
        self._config = config or RalphConfig()
        self._cancelled = False

    @property
    def config(self) -> RalphConfig:
        return self._config

    def cancel(self) -> None:
        """Request cancellation of the running loop."""
        self._cancelled = True

    async def run(
        self,
        initial_input: str,
        pge_runner: PGECycleRunner,
    ) -> RalphResult:
        """Execute the Ralph Loop.

        Args:
            initial_input: The original user message/task.
            pge_runner: Callable that runs a single PGE cycle.

        Returns:
            RalphResult with accumulated iteration history.
        """
        iterations: list[IterationRecord] = []
        current_input = initial_input
        total_start = time.monotonic()
        final_response = ""
        stop_reason = ""
        converged = False

        # Track tool signatures for progress detection
        recent_tool_sigs: list[str] = []

        for i in range(self._config.max_iterations):
            if self._cancelled:
                stop_reason = "cancelled"
                log.info("ralph_cancelled", iteration=i)
                break

            # Total budget check
            elapsed_total = time.monotonic() - total_start
            if elapsed_total >= self._config.total_budget_seconds:
                stop_reason = "total_budget_exceeded"
                log.info(
                    "ralph_total_budget",
                    elapsed=elapsed_total,
                    budget=self._config.total_budget_seconds,
                )
                break

            # Run single PGE cycle
            iter_start = time.monotonic()

            try:
                response, tools_called = await pge_runner(
                    current_input,
                    ralph_prompt=RALPH_PROMPT_FRAGMENT,
                )
            except TimeoutError:
                stop_reason = "iteration_timeout"
                log.warning("ralph_iteration_timeout", iteration=i)
                break
            except Exception:
                stop_reason = "error"
                log.exception("ralph_pge_error", iteration=i)
                break

            iter_duration = time.monotonic() - iter_start

            # Per-iteration budget check
            if iter_duration > self._config.iteration_budget_seconds:
                log.info(
                    "ralph_iteration_over_budget",
                    iteration=i,
                    duration=iter_duration,
                    budget=self._config.iteration_budget_seconds,
                )
                # Don't break -- record this iteration but check budget on next

            # Parse signal
            signal, detail = parse_signal(response)

            record = IterationRecord(
                iteration=i,
                tools_called=tools_called,
                output_summary=response[:200],
                duration_seconds=iter_duration,
                signal=signal,
                next_step=detail if signal == RalphSignal.CONTINUE else "",
            )
            iterations.append(record)
            final_response = response

            log.info(
                "ralph_iteration",
                iteration=i,
                signal=signal.value,
                tools=len(tools_called),
                duration=round(iter_duration, 2),
            )

            # Check for STOP
            if signal == RalphSignal.STOP:
                stop_reason = "completed"
                converged = True
                break

            # Check for no signal (implicit stop)
            if signal == RalphSignal.NONE:
                stop_reason = "no_signal"
                break

            # Progress detection: identical tool calls
            if self._config.require_progress:
                sig = _tools_signature(tools_called)
                recent_tool_sigs.append(sig)
                if len(recent_tool_sigs) >= IDENTICAL_ITERATION_THRESHOLD:
                    tail = recent_tool_sigs[-IDENTICAL_ITERATION_THRESHOLD:]
                    if len(set(tail)) == 1 and tail[0]:
                        stop_reason = "no_progress"
                        log.info(
                            "ralph_no_progress",
                            iteration=i,
                            repeated_tools=tail[0],
                        )
                        break

            # CONTINUE: feed next step as input
            current_input = (
                detail if detail else f"Continue the task. Previous output: {response[:500]}"
            )
        else:
            # Exhausted max iterations
            stop_reason = "max_iterations"
            log.info("ralph_max_iterations", max=self._config.max_iterations)

        total_duration = time.monotonic() - total_start

        result = RalphResult(
            final_response=final_response,
            iterations=iterations,
            total_duration_seconds=total_duration,
            stop_reason=stop_reason,
            converged=converged,
        )

        log.info(
            "ralph_complete",
            iterations=len(iterations),
            stop_reason=stop_reason,
            converged=converged,
            duration=round(total_duration, 2),
        )

        return result


# ============================================================================
# Gateway integration helper
# ============================================================================


async def run_ralph_loop(
    initial_input: str,
    pge_runner: PGECycleRunner,
    config: RalphConfig | None = None,
) -> RalphResult:
    """Convenience function to run a Ralph Loop.

    Intended as the integration point for the Gateway -- call this instead
    of a single PGE cycle when autonomous multi-step mode is needed.

    Args:
        initial_input: The user's task/message.
        pge_runner: A callable that runs one PGE cycle.
        config: Optional RalphConfig overrides.

    Returns:
        RalphResult with full iteration history.
    """
    loop = RalphLoop(config=config)
    return await loop.run(initial_input, pge_runner)
