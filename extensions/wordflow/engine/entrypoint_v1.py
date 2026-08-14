# -*- coding: utf-8 -*-
"""entrypoint_v1 — V1-04. Unique public entry to OrchestratorV1. 0% LLM."""
from __future__ import annotations

from typing import Any

from .orchestrator_v1 import OrchestratorV1

_DEFAULT: OrchestratorV1 | None = None


def get_orchestrator() -> OrchestratorV1:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = OrchestratorV1()
    return _DEFAULT


def run_v1(
    raw_input: str,
    *,
    topic: str | None = None,
    operation: str = "READ_LOCAL",
    risk_score: int = 0,
    band: str = "",
    task_class: str | None = None,
    attempts: int = 0,
    orchestrator: OrchestratorV1 | None = None,
) -> dict[str, Any]:
    """Single call: raw text → full V1 turn result."""
    orch = orchestrator or get_orchestrator()
    return orch.run_turn(
        raw_input,
        topic or raw_input[:80],
        operation=operation,
        risk_score=risk_score,
        band=band,
        task_class=task_class,
        attempts=attempts,
    )


def reset_default() -> None:
    """Test helper: drop singleton."""
    global _DEFAULT
    _DEFAULT = None
