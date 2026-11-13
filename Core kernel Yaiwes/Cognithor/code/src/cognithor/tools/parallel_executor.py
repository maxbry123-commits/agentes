"""Parallel tool call execution via asyncio.gather().

Multiple MCP tools fire simultaneously when safe. State-mutating tools
are still executed sequentially. Partial results are returned on failure.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from cognithor.tools.parallel_policy import is_parallelizable
from cognithor.utils.logging import get_logger

log = get_logger(__name__)

DEFAULT_TOOL_TIMEOUT_SECONDS = 30


@dataclass
class ToolCall:
    """A single tool invocation request."""

    tool_name: str
    params: dict[str, Any] = field(default_factory=dict)
    call_id: str = ""


@dataclass
class ToolResult:
    """Result of a tool invocation."""

    call_id: str
    tool_name: str
    output: Any = None
    error: str | None = None
    success: bool = True
    duration_ms: float = 0.0


async def execute_single(
    call: ToolCall,
    executor_fn: Any,
    timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS,
) -> ToolResult:
    """Execute a single tool call with timeout."""
    import time

    start = time.monotonic()
    try:
        result = await asyncio.wait_for(
            executor_fn(call.tool_name, call.params),
            timeout=timeout_seconds,
        )
        duration = (time.monotonic() - start) * 1000
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            output=result,
            success=True,
            duration_ms=duration,
        )
    except TimeoutError:
        duration = (time.monotonic() - start) * 1000
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            error=f"Timeout after {timeout_seconds}s",
            success=False,
            duration_ms=duration,
        )
    except Exception as exc:
        duration = (time.monotonic() - start) * 1000
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            error=str(exc),
            success=False,
            duration_ms=duration,
        )


def partition_calls(
    calls: list[ToolCall],
) -> tuple[list[ToolCall], list[ToolCall]]:
    """Split tool calls into parallelizable and sequential groups."""
    parallel: list[ToolCall] = []
    sequential: list[ToolCall] = []
    for call in calls:
        if is_parallelizable(call.tool_name):
            parallel.append(call)
        else:
            sequential.append(call)
    return parallel, sequential


async def execute_tool_calls(
    calls: list[ToolCall],
    executor_fn: Any,
    timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS,
) -> list[ToolResult]:
    """Execute tool calls with parallelization where safe.

    Read-only tools run concurrently via ``asyncio.gather()``.
    State-mutating tools run sequentially afterward.
    Results are returned in the original call order.

    Args:
        calls: Ordered list of tool calls.
        executor_fn: Async callable ``(tool_name, params) -> result``.
        timeout_seconds: Per-tool timeout.

    Returns:
        List of ToolResult in the same order as ``calls``.
    """
    if not calls:
        return []

    parallel, sequential = partition_calls(calls)

    # Execute parallel tools concurrently
    parallel_results: list[ToolResult] = []
    if parallel:
        tasks = [execute_single(c, executor_fn, timeout_seconds) for c in parallel]
        parallel_results = list(await asyncio.gather(*tasks, return_exceptions=False))

    # Execute sequential tools one by one
    sequential_results: list[ToolResult] = []
    for call in sequential:
        result = await execute_single(call, executor_fn, timeout_seconds)
        sequential_results.append(result)

    # Merge back in original order
    result_map: dict[str, ToolResult] = {}
    for r in parallel_results + sequential_results:
        result_map[r.call_id] = r

    return [result_map[c.call_id] for c in calls if c.call_id in result_map]
