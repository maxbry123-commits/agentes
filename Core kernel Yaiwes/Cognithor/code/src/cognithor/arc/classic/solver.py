"""ARC-AGI-3 Solver: DSL search + LLM fallback orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cognithor.arc.classic.dsl_search import search as dsl_search
from cognithor.arc.classic.llm_solver import LLMSolver
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.arc.classic.task_parser import ArcTask, Solution

__all__ = ["ArcSolver"]

log = get_logger(__name__)


class ArcSolver:
    """Solves ARC-AGI-3 tasks via DSL search + LLM code-generation fallback."""

    def __init__(self, llm_fn: Any | None = None) -> None:
        # llm_fn is accepted for API compatibility but not forwarded;
        # LLMSolver uses its own internal _llm_call which tests can mock.
        self._llm_solver = LLMSolver()

    async def solve(self, task: ArcTask) -> list[Solution]:
        """Return up to 3 candidate solutions, ranked by confidence."""
        # Phase 1: DSL search
        dsl_solutions = dsl_search(task, max_depth=3)
        if dsl_solutions:
            log.info(
                "arc_dsl_solved",
                task=task.task_id,
                count=len(dsl_solutions),
                best=dsl_solutions[0].description,
            )
            return self._rank(dsl_solutions)[:3]

        # Phase 2: LLM fallback
        log.info("arc_dsl_no_solution", task=task.task_id, fallback="llm")
        llm_solutions = await self._llm_solver.solve(task)
        if llm_solutions:
            log.info("arc_llm_solved", task=task.task_id, count=len(llm_solutions))
            return self._rank(llm_solutions)[:3]

        log.warning("arc_no_solution", task=task.task_id)
        return []

    @staticmethod
    def _rank(solutions: list[Solution]) -> list[Solution]:
        """Occam's Razor: lower complexity first, DSL before LLM."""
        return sorted(
            solutions,
            key=lambda s: (s.complexity, 0 if s.method.startswith("dsl") else 1),
        )
