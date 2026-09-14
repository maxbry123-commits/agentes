"""Tests for the combinatorial DSL search engine."""

from __future__ import annotations

import time

from cognithor.arc.classic.dsl_search import (
    _grids_equal,
    build_candidates,
    search,
)
from cognithor.arc.classic.task_parser import ArcTask

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(
    examples: list[tuple[list[list[int]], list[list[int]]]],
    test_input: list[list[int]],
    task_id: str = "test",
) -> ArcTask:
    return ArcTask(task_id=task_id, examples=examples, test_input=test_input)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGridsEqual:
    def test_identical(self):
        assert _grids_equal([[1, 2], [3, 4]], [[1, 2], [3, 4]])

    def test_different_values(self):
        assert not _grids_equal([[1, 2]], [[1, 3]])

    def test_different_rows(self):
        assert not _grids_equal([[1, 2]], [[1, 2], [3, 4]])

    def test_different_cols(self):
        assert not _grids_equal([[1, 2, 3]], [[1, 2]])


class TestBuildCandidates:
    def test_returns_list(self):
        cands = build_candidates()
        assert isinstance(cands, list)
        assert len(cands) > 100  # Should have 170+ candidates

    def test_restricts_to_example_colors(self):
        # Only colors 0, 1 appear -> far fewer recolor combos
        examples = [([[0, 1], [1, 0]], [[1, 0], [0, 1]])]
        cands = build_candidates(examples)
        restricted = build_candidates()
        assert len(cands) < len(restricted)


class TestFindsSingleRotation:
    def test_finds_rotate_90(self):
        # rotate_90: [[1,2],[3,4]] -> [[3,1],[4,2]]
        inp = [[1, 2], [3, 4]]
        out = [[3, 1], [4, 2]]
        task = _make_task(
            examples=[(inp, out)],
            test_input=[[5, 6], [7, 8]],
        )
        solutions = search(task, timeout=10.0)
        assert len(solutions) >= 1
        names = [s.description for s in solutions]
        assert any("rotate_90" in n for n in names)


class TestFindsFlipH:
    def test_finds_flip_h(self):
        inp = [[1, 2, 3], [4, 5, 6]]
        out = [[3, 2, 1], [6, 5, 4]]
        task = _make_task(
            examples=[(inp, out)],
            test_input=[[7, 8, 9], [0, 1, 2]],
        )
        solutions = search(task, timeout=10.0)
        assert len(solutions) >= 1
        names = [s.description for s in solutions]
        assert any("flip_h" in n for n in names)


class TestFindsRecolor:
    def test_finds_recolor_1_5(self):
        inp = [[0, 1, 0], [1, 1, 0]]
        out = [[0, 5, 0], [5, 5, 0]]
        # Second example to confirm
        inp2 = [[1, 0], [0, 1]]
        out2 = [[5, 0], [0, 5]]
        task = _make_task(
            examples=[(inp, out), (inp2, out2)],
            test_input=[[1, 1], [0, 0]],
        )
        solutions = search(task, timeout=10.0)
        assert len(solutions) >= 1
        names = [s.description for s in solutions]
        assert any("recolor(1,5)" in n for n in names)
        # Check the output is correct
        recolor_sol = next(s for s in solutions if "recolor(1,5)" in s.description)
        assert recolor_sol.output == [[5, 5], [0, 0]]


class TestFindsDepth2Combo:
    def test_finds_flip_h_then_recolor(self):
        # flip_h then recolor(1,5): [[1,0]] -> flip_h -> [[0,1]] -> recolor -> [[0,5]]
        inp = [[1, 0, 2], [0, 1, 0]]
        # flip_h: [[2,0,1],[0,1,0]], then recolor(1,5): [[2,0,5],[0,5,0]]
        out = [[2, 0, 5], [0, 5, 0]]

        inp2 = [[0, 1], [1, 2]]
        # flip_h: [[1,0],[2,1]], then recolor(1,5): [[5,0],[2,5]]
        out2 = [[5, 0], [2, 5]]

        task = _make_task(
            examples=[(inp, out), (inp2, out2)],
            test_input=[[1, 2], [0, 1]],
        )
        solutions = search(task, timeout=30.0, max_depth=2)
        assert len(solutions) >= 1
        # Should find a depth-2 solution
        assert any(s.complexity == 2 for s in solutions)


class TestNoSolutionReturnsEmpty:
    def test_unsolvable(self):
        # A task where each cell is shifted by its position — no DSL combo does this
        inp1 = [[1, 2], [3, 4]]
        out1 = [[2, 4], [6, 8]]  # each cell doubled — no DSL op does element-wise math

        inp2 = [[5, 1], [0, 3]]
        out2 = [[9, 2], [0, 7]]  # NOT doubled — contradicts doubling hypothesis too

        task = _make_task(
            examples=[(inp1, out1), (inp2, out2)],
            test_input=[[1, 1], [1, 1]],
        )
        solutions = search(task, timeout=2.0, max_depth=2)
        assert solutions == []


class TestValidatesAgainstAllExamples:
    def test_must_match_all_examples(self):
        # rotate_90 matches first example but NOT second
        inp1 = [[1, 2], [3, 4]]
        out1 = [[3, 1], [4, 2]]  # This IS rotate_90

        inp2 = [[5, 6], [7, 8]]
        out2 = [[0, 0], [0, 0]]  # This is NOT rotate_90

        task = _make_task(
            examples=[(inp1, out1), (inp2, out2)],
            test_input=[[1, 1], [1, 1]],
        )
        solutions = search(task, timeout=5.0, max_depth=1)
        # rotate_90 should NOT appear because it fails example 2
        names = [s.description for s in solutions]
        assert "rotate_90" not in names


class TestRankedByComplexity:
    def test_simpler_first(self):
        # flip_h is depth-1; any depth-2 solution should come after
        inp = [[1, 2, 3], [4, 5, 6]]
        out = [[3, 2, 1], [6, 5, 4]]
        task = _make_task(
            examples=[(inp, out)],
            test_input=[[7, 8, 9], [0, 1, 2]],
        )
        solutions = search(task, timeout=10.0, max_depth=1)
        assert len(solutions) >= 1
        # All depth-1 solutions should be complexity 1
        for s in solutions:
            assert s.complexity == 1
        # First solution should have lowest complexity
        assert solutions[0].complexity <= solutions[-1].complexity


class TestTimeoutRespected:
    def test_does_not_hang(self):
        # A task with no solution — search should respect timeout
        inp = [[1, 2], [3, 4]]
        out = [[9, 8], [7, 6]]  # Unlikely to match any single/double DSL op
        task = _make_task(
            examples=[(inp, out)],
            test_input=[[0, 0], [0, 0]],
        )
        start = time.monotonic()
        _solutions = search(task, timeout=2.0, max_depth=3)
        elapsed = time.monotonic() - start
        # Should finish within timeout + small margin
        assert elapsed < 5.0
