"""Tests for ARC-AGI-3 task data model."""

from __future__ import annotations

from cognithor.arc.classic.task_parser import ArcTask, GameResult, Solution


class TestArcTask:
    def test_create_task(self):
        task = ArcTask(
            task_id="test_001",
            examples=[([[1, 0], [0, 1]], [[0, 1], [1, 0]])],
            test_input=[[1, 1], [0, 0]],
        )
        assert task.task_id == "test_001"
        assert len(task.examples) == 1

    def test_task_with_multiple_examples(self):
        task = ArcTask(
            task_id="test_002",
            examples=[
                ([[1, 0], [0, 1]], [[0, 1], [1, 0]]),
                ([[2, 0], [0, 2]], [[0, 2], [2, 0]]),
            ],
            test_input=[[3, 0], [0, 3]],
        )
        assert len(task.examples) == 2


class TestSolution:
    def test_create_solution(self):
        sol = Solution(output=[[0, 1], [1, 0]], method="dsl", description="flip_h", complexity=1)
        assert sol.method == "dsl"
        assert sol.complexity == 1

    def test_solution_ordering_by_complexity(self):
        s1 = Solution(output=[[1]], method="dsl", description="a", complexity=1)
        s2 = Solution(output=[[2]], method="dsl", description="b", complexity=3)
        s3 = Solution(output=[[3]], method="llm", description="c", complexity=2)
        ranked = sorted([s3, s1, s2], key=lambda s: (s.complexity, s.method != "dsl"))
        assert ranked[0] is s1
        assert ranked[1] is s3


class TestGameResult:
    def test_create_result(self):
        r = GameResult(win=True, attempts=1, task_id="test")
        assert r.win is True
        assert r.solutions_tried == []
