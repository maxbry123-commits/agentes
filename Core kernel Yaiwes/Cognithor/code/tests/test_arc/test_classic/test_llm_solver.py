"""Tests for the LLM code-generation ARC solver."""

from __future__ import annotations

import pytest

from cognithor.arc.classic.llm_solver import LLMSolver
from cognithor.arc.classic.task_parser import ArcTask

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# rotate_90: transposed + each row reversed  -> classic 90-degree CW rotation
_ROTATE_90_CODE = """\
def transform(grid):
    rows = len(grid)
    cols = len(grid[0])
    return [[grid[rows - 1 - r][c] for r in range(rows)] for c in range(cols)]
"""

_ROTATE_TASK = ArcTask(
    task_id="rotate_test",
    examples=[
        (
            [[1, 2], [3, 4]],
            [[3, 1], [4, 2]],
        ),
        (
            [[5, 6], [7, 8]],
            [[7, 5], [8, 6]],
        ),
    ],
    test_input=[[9, 0], [1, 2]],
)


def _make_solver_with_mock(code_response: str) -> LLMSolver:
    """Return an LLMSolver whose _llm_call always returns *code_response*."""

    class _MockSolver(LLMSolver):
        async def _llm_call(self, prompt: str) -> str:
            return f"```python\n{code_response}\n```"

    return _MockSolver()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_solve_with_valid_code():
    """LLM returns valid rotate_90 code -> solution list is non-empty."""
    solver = _make_solver_with_mock(_ROTATE_90_CODE)
    solutions = await solver.solve(_ROTATE_TASK)

    assert len(solutions) == 1
    sol = solutions[0]
    assert sol.method == "llm"
    # rotate [[9,0],[1,2]] 90 CW: col 0 bottom->top = [1,9], col 1 bottom->top = [2,0]
    assert sol.output == [[1, 9], [2, 0]]


@pytest.mark.asyncio
async def test_invalid_code_returns_empty():
    """LLM returns garbage Python -> solve returns empty list."""

    class _GarbageSolver(LLMSolver):
        async def _llm_call(self, prompt: str) -> str:
            return "```python\nthis is not python !!!\n```"

    solver = _GarbageSolver()
    task = ArcTask(
        task_id="garbage_test",
        examples=[([[1]], [[1]])],
        test_input=[[1]],
    )
    solutions = await solver.solve(task, max_attempts=1)
    assert solutions == []


def test_code_sandbox_blocks_imports():
    """Code containing 'import os' is rejected by _is_safe."""
    solver = LLMSolver()
    unsafe_code = "import os\ndef transform(grid):\n    return grid\n"
    assert solver._is_safe(unsafe_code) is False


def test_extract_python_from_markdown():
    """_extract_python pulls code from a fenced block."""
    solver = LLMSolver()
    response = "Some text\n```python\ndef transform(grid):\n    return grid\n```\nTrailing."
    code = solver._extract_python(response)
    assert "def transform" in code
    assert "```" not in code


def test_extract_python_no_code_block():
    """_extract_python returns empty string when no fenced block is present."""
    solver = LLMSolver()
    assert solver._extract_python("No code here at all.") == ""
    assert solver._extract_python("") == ""


def test_format_task_includes_grids():
    """_format_task produces a prompt that mentions all example grids."""
    solver = LLMSolver()
    prompt = solver._format_task(_ROTATE_TASK)

    # All example inputs/outputs should appear as repr'd lists.
    assert "[[1, 2], [3, 4]]" in prompt
    assert "[[3, 1], [4, 2]]" in prompt
    assert "[[5, 6], [7, 8]]" in prompt
    assert "[[7, 5], [8, 6]]" in prompt
    # transform instruction
    assert "transform" in prompt
