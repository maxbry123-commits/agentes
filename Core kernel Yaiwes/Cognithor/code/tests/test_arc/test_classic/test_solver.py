"""Tests for ARC-AGI-3 ArcSolver orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from cognithor.arc.classic.solver import ArcSolver
from cognithor.arc.classic.task_parser import ArcTask


class TestArcSolver:
    @pytest.mark.asyncio
    async def test_dsl_solution_found(self):
        task = ArcTask(
            task_id="rot",
            examples=[([[1, 2], [3, 4]], [[3, 1], [4, 2]])],
            test_input=[[5, 6], [7, 8]],
        )
        solver = ArcSolver()
        solutions = await solver.solve(task)
        assert len(solutions) >= 1
        assert solutions[0].method.startswith("dsl")

    @pytest.mark.asyncio
    async def test_llm_fallback_when_dsl_fails(self):
        # This task has no DSL-primitive solution: output size differs from input
        # and doesn't match any rotation/flip/tile/scale pattern.
        task = ArcTask(
            task_id="complex",
            examples=[([[1, 2, 3]], [[7, 8]])],
            test_input=[[4, 5, 6]],
        )
        solver = ArcSolver()
        solver._llm_solver._llm_call = AsyncMock(
            return_value=(
                "```python\n"
                "def transform(grid):\n"
                "    return [[c * 99 for c in row] for row in grid]\n"
                "```"
            )
        )
        await solver.solve(task)
        solver._llm_solver._llm_call.assert_called()

    @pytest.mark.asyncio
    async def test_returns_max_3(self):
        task = ArcTask(
            task_id="rot",
            examples=[([[1, 2], [3, 4]], [[3, 1], [4, 2]])],
            test_input=[[5, 6], [7, 8]],
        )
        solver = ArcSolver()
        solutions = await solver.solve(task)
        assert len(solutions) <= 3

    @pytest.mark.asyncio
    async def test_dsl_before_llm_in_ranking(self):
        task = ArcTask(
            task_id="rot",
            examples=[([[1, 2], [3, 4]], [[3, 1], [4, 2]])],
            test_input=[[5, 6], [7, 8]],
        )
        solver = ArcSolver()
        solutions = await solver.solve(task)
        if solutions:
            assert solutions[0].method.startswith("dsl")

    @pytest.mark.asyncio
    async def test_no_solution_returns_empty(self):
        task = ArcTask(
            task_id="impossible",
            examples=[([[1, 2], [3, 4]], [[99, 98, 97]])],
            test_input=[[5]],
        )
        solver = ArcSolver()
        solver._llm_solver._llm_call = AsyncMock(return_value="I cannot solve this.")
        solutions = await solver.solve(task)
        assert solutions == []
