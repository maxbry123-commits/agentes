# -*- coding: utf-8 -*-
"""Forensic workflow gap audit for the programming pipeline.

Deterministic repository-level checks for Wordflow's code workflow. The audit
only reports machine-verifiable gaps and prepares explicit fix metadata; it does
not declare PASS (VerdictAuthority remains the only PASS authority).
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class WorkflowGap:
    gap_id: str
    severity: str
    title: str
    evidence: str
    solution: str
    status: str = "OPEN"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


REQUIRED_DOCS = (
    "PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md",
    "PIPELINE/FORENSIC_CODE_AUDIT.md",
    "PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md",
)

REQUIRED_PIPELINE_FILES = (
    "extensions/wordflow/engine/programming_pipeline.py",
    "extensions/wordflow/engine/code_path_runner.py",
    "extensions/wordflow/standards/executor_gates.py",
    "extensions/wordflow/standards/verdict_authority.py",
    "extensions/wordflow/standards/copy_first.py",
)


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def _missing_paths(root: Path, paths: Iterable[str]) -> list[str]:
    return [p for p in paths if not _exists(root, p)]


def audit_programming_workflow(root: Path | str | None = None) -> dict[str, Any]:
    """Audit Wordflow programming workflow wiring and prepare gap fixes.

    Returns a fail-closed packet with ``gaps`` and ``solutions_prepared``. A
    clean audit is ``ok=True`` but still uses ``verdict=NO_PASS_CLAIM`` so the
    caller cannot confuse this analyzer with VerdictAuthority.
    """
    repo_root = Path(root or Path(__file__).resolve().parents[3]).resolve()
    gaps: list[WorkflowGap] = []

    missing_docs = _missing_paths(repo_root, REQUIRED_DOCS)
    if missing_docs:
        gaps.append(
            WorkflowGap(
                "WF-AUD-001",
                "BLOCK",
                "authority_documents_missing",
                ",".join(missing_docs),
                "Restore authority docs or block programming workflow before IMPLEMENT.",
            )
        )

    missing_files = _missing_paths(repo_root, REQUIRED_PIPELINE_FILES)
    if missing_files:
        gaps.append(
            WorkflowGap(
                "WF-AUD-002",
                "BLOCK",
                "pipeline_code_paths_missing",
                ",".join(missing_files),
                "Restore required code paths and wire them from ProgrammingPipeline.",
            )
        )

    # Import here to audit the actual runtime signatures after basic path checks.
    from extensions.wordflow.engine.code_path_runner import run_code_path
    from extensions.wordflow.engine.programming_pipeline import KNOWN_KW

    runner_kwargs = {
        name
        for name, param in inspect.signature(run_code_path).parameters.items()
        if name != "raw_input" and param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD)
    }
    known = set(KNOWN_KW)
    passthrough_missing = sorted(runner_kwargs - known)
    if passthrough_missing:
        gaps.append(
            WorkflowGap(
                "WF-AUD-003",
                "BLOCK",
                "unified_kwargs_passthrough_gap",
                ",".join(passthrough_missing),
                "Add every run_code_path keyword to KNOWN_KW or explicitly translate it before dispatch.",
            )
        )

    pre_gate_extra = sorted(known - runner_kwargs - {"pre_gate_done"})
    if pre_gate_extra:
        gaps.append(
            WorkflowGap(
                "WF-AUD-004",
                "P1",
                "unknown_unified_kwargs_not_runner_owned",
                ",".join(pre_gate_extra),
                "Document local-only kwargs or remove them from KNOWN_KW.",
            )
        )

    solutions = [g.to_dict() for g in gaps]
    return {
        "ok": not any(g.severity == "BLOCK" for g in gaps),
        "repo_root": str(repo_root),
        "gap_count": len(gaps),
        "blocking_gap_count": sum(1 for g in gaps if g.severity == "BLOCK"),
        "gaps": [g.to_dict() for g in gaps],
        "solutions_prepared": solutions,
        "verdict": "NO_PASS_CLAIM",
        "authority": "WorkflowGapAudit; PASS reserved for VerdictAuthority",
    }
