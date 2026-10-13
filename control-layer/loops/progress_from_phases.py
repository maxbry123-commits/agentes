"""Progress desde outputs reales de fase · 0% LLM
SOURCE: mejora E · adaptive deja de ser ciego
"""
from __future__ import annotations
from typing import Any

from loops.phases import PhaseResult
from loops.progress import ProgressEvaluator
from loops.contracts.types import ProgressResult


def extract_progress_signal(phase_results: list[PhaseResult]) -> tuple[str, Any]:
    """
    Prioridad:
    1. tests dict {passed, total} en cualquier output
    2. validation boolean
    3. evidence count
    4. agent_output presence
    5. sheriff-like all required ok → boolean
    """
    by = {r.phase: r for r in phase_results}

    # scan all outputs for tests
    for r in phase_results:
        out = r.output or {}
        for key in ("tests", "test_results", "pytest"):
            if key in out and isinstance(out[key], dict) and out[key].get("total"):
                return "tests", out[key]
        # nested agent_output
        ao = out.get("agent_output") or out.get("ejecutar") or {}
        if isinstance(ao, dict):
            for key in ("tests", "test_results"):
                if key in ao and isinstance(ao[key], dict) and ao[key].get("total"):
                    return "tests", ao[key]

    val = by.get("validar")
    if val is not None:
        return "validation", bool(val.ok)

    evid = by.get("evidencia")
    if evid and evid.output:
        ev = evid.output.get("evidence") or evid.output
        if isinstance(ev, dict):
            # count non-empty values
            n = sum(1 for v in ev.values() if v)
            return "evidence", n
        if isinstance(ev, list):
            return "evidence", len(ev)

    ejec = by.get("ejecutar")
    if ejec is not None:
        return "boolean", bool(ejec.ok and (ejec.output.get("agent_output") or ejec.output.get("ejecutar")))

    return "boolean", all(r.ok for r in phase_results if not r.skipped)


def progress_from_phases(
    phase_results: list[PhaseResult],
    *,
    evaluator: ProgressEvaluator | None = None,
    prev_score: float | None = None,
    threshold: float = 0.1,
) -> ProgressResult:
    ev = evaluator or ProgressEvaluator()
    kind, value = extract_progress_signal(phase_results)
    return ev.evaluate(kind=kind, value=value, prev_score=prev_score, threshold=threshold)
