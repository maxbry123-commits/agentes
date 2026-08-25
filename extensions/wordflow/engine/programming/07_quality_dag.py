# -*- coding: utf-8 -*-
"""Process 07 — QualityDAG."""
from __future__ import annotations

from typing import Any


def run_quality_dag(
    *,
    run_quality_dag_flag: bool,
    quality_dag_ok: bool,
    scan_paths: list[str] | None,
    adapted_dest: str,
    wire_trace: dict[str, Any],
) -> bool:
    from extensions.wordflow.standards.quality_dag import QualityDAG
    from extensions.wordflow.standards.quality_handlers import register_deterministic_handlers

    paths_for_q = list(scan_paths or [])
    if adapted_dest:
        paths_for_q.append(adapted_dest)
    paths_for_q.append("extensions/wordflow/engine/programming/runner.py")

    dag_passed = bool(quality_dag_ok)
    if run_quality_dag_flag:
        dag = QualityDAG()
        register_deterministic_handlers(dag, paths=paths_for_q, quality_dag_ok=quality_dag_ok)
        dag_results = dag.run(fail_closed=True)
        dag_passed = dag.passed(dag_results) and quality_dag_ok
        wire_trace["quality_dag"] = {
            "passed": dag_passed,
            "results": [
                {"name": r.name, "status": r.status.value, "detail": r.detail}
                for r in dag_results
            ],
        }
    return dag_passed
