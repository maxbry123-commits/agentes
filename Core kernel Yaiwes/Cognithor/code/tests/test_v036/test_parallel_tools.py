"""Tests for Feature 5: Parallel Tool Calls."""

from __future__ import annotations

import asyncio
import time

import pytest

from cognithor.tools.parallel_executor import (
    ToolCall,
    execute_single,
    execute_tool_calls,
    partition_calls,
)
from cognithor.tools.parallel_policy import is_parallelizable


class TestParallelPolicy:
    def test_read_tools_are_parallelizable(self):
        for tool in ["web_search", "read_file", "search_memory", "git_status"]:
            assert is_parallelizable(tool), f"{tool} should be parallelizable"

    def test_write_tools_are_sequential(self):
        for tool in ["write_file", "exec_command", "save_to_memory", "git_commit"]:
            assert not is_parallelizable(tool), f"{tool} should be sequential"

    def test_unknown_tool_defaults_sequential(self):
        assert not is_parallelizable("totally_unknown_tool_xyz")

    def test_mcp_read_pattern(self):
        assert is_parallelizable("mcp_slack_read")
        assert not is_parallelizable("mcp_slack_write")


class TestPartition:
    def test_partition_separates_correctly(self):
        calls = [
            ToolCall(tool_name="read_file", call_id="1"),
            ToolCall(tool_name="write_file", call_id="2"),
            ToolCall(tool_name="web_search", call_id="3"),
        ]
        par, seq = partition_calls(calls)
        assert len(par) == 2
        assert len(seq) == 1
        assert seq[0].tool_name == "write_file"


class TestExecution:
    @pytest.mark.asyncio
    async def test_parallel_reads_faster_than_sequential(self):
        """Parallel read tools should complete faster than if run sequentially."""
        delay = 0.05  # 50ms per tool

        async def slow_executor(name, params):
            await asyncio.sleep(delay)
            return f"result:{name}"

        calls = [ToolCall(tool_name="read_file", params={}, call_id=f"r{i}") for i in range(5)]

        start = time.monotonic()
        results = await execute_tool_calls(calls, slow_executor, timeout_seconds=5)
        elapsed = time.monotonic() - start

        assert len(results) == 5
        assert all(r.success for r in results)
        # 5 parallel calls at 50ms each should take ~50ms, not ~250ms
        assert elapsed < delay * 4, f"Took {elapsed:.3f}s — should be parallel"

    @pytest.mark.asyncio
    async def test_sequential_tools_still_work(self):
        """Sequential tools execute one by one."""
        call_order: list[str] = []

        async def tracking_executor(name, params):
            call_order.append(name)
            return "ok"

        calls = [
            ToolCall(tool_name="write_file", call_id="w1"),
            ToolCall(tool_name="exec_command", call_id="w2"),
        ]
        results = await execute_tool_calls(calls, tracking_executor)
        assert len(results) == 2
        assert all(r.success for r in results)
        assert call_order == ["write_file", "exec_command"]

    @pytest.mark.asyncio
    async def test_partial_failure_returns_partial_results(self):
        """If one parallel tool fails, others still return results."""

        async def flaky_executor(name, params):
            if name == "web_search":
                raise ValueError("search failed")
            return f"ok:{name}"

        calls = [
            ToolCall(tool_name="read_file", call_id="1"),
            ToolCall(tool_name="web_search", call_id="2"),
            ToolCall(tool_name="search_memory", call_id="3"),
        ]
        results = await execute_tool_calls(calls, flaky_executor)
        assert len(results) == 3
        success = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        assert len(success) == 2
        assert len(failed) == 1
        assert failed[0].tool_name == "web_search"

    @pytest.mark.asyncio
    async def test_timeout_respected_per_tool(self):
        """Per-tool timeout kills hung tools."""

        async def hanging_executor(name, params):
            await asyncio.sleep(10)
            return "should not reach"

        call = ToolCall(tool_name="read_file", call_id="t1")
        result = await execute_single(call, hanging_executor, timeout_seconds=0.1)
        assert not result.success
        assert "Timeout" in result.error

    @pytest.mark.asyncio
    async def test_empty_calls_returns_empty(self):
        async def noop(name, params):
            return None

        results = await execute_tool_calls([], noop)
        assert results == []

    @pytest.mark.asyncio
    async def test_mixed_parallel_sequential_preserves_order(self):
        """Results come back in original call order."""

        async def echo(name, params):
            return name

        calls = [
            ToolCall(tool_name="read_file", call_id="a"),
            ToolCall(tool_name="write_file", call_id="b"),
            ToolCall(tool_name="web_search", call_id="c"),
        ]
        results = await execute_tool_calls(calls, echo)
        assert [r.call_id for r in results] == ["a", "b", "c"]
