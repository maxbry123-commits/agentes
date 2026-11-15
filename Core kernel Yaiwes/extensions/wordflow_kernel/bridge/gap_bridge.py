"""Bridge: maxbry_loop gaps / tasks → kernel TaskSpec → code_path jobs.

Continuous loop discovers gaps; this module turns them into kernel-executable
TaskSpec list consumable by mission_planner / code_path_runner.
"""
from __future__ import annotations

from typing import Any, Iterable

from wordflow_kernel.models import TaskSpec, uid
from wordflow_kernel.gap_tasks import GapTaskCompiler
from wordflow_kernel.models import AuditReport, Gap, Evidence


def loop_tasks_to_taskspecs(loop_tasks: Iterable[Any], workspace_id: str) -> list[TaskSpec]:
    """Convert maxbry_loop Task objects (or dicts) to kernel TaskSpec."""
    out: list[TaskSpec] = []
    for t in loop_tasks:
        if hasattr(t, "id"):
            tid = t.id
            title = t.title
            desc = t.description
            status = t.status
            acceptance = tuple(t.acceptance or ())
        else:
            tid = t.get("id", uid("task"))
            title = t.get("title", "")
            desc = t.get("description", "")
            status = t.get("status", "pending")
            acceptance = tuple(t.get("acceptance") or ())
        out.append(
            TaskSpec(
                task_id=tid if tid.startswith("task_") else uid("task"),
                gap_id=tid,
                objective=title or desc,
                target="code_path",
                acceptance=acceptance
                or ("evidence recorded", "code_path claim PASS"),
                status="PENDING" if status in ("pending", "ready") else status.upper(),
                workspace_id=workspace_id,
            )
        )
    return out


def synthetic_report_from_loop_gaps(
    mission_id: str,
    gap_pairs: list[tuple[str, str]],
) -> AuditReport:
    """Build AuditReport from (kind, description) gap pairs for GapTaskCompiler."""
    gaps = [
        Gap(
            gap_id=uid("gap"),
            requirement=desc,
            status="MISSING",
            severity="MEDIUM",
            recommendation=f"Resolve [{kind}]: {desc[:120]}",
        )
        for kind, desc in gap_pairs
    ]
    return AuditReport(
        audit_id=uid("audit"),
        target=mission_id,
        revision="loop",
        status="GAPS_FOUND" if gaps else "PASS",
        claims_checked=len(gaps),
        matches=0,
        partial=0,
        missing=len(gaps),
        contradictions=0,
        gaps=gaps,
        evidence=[Evidence(uid("ev"), "loop_gap", detail={"count": len(gaps)})],
    )


def gaps_to_taskspecs(gap_pairs: list[tuple[str, str]], workspace_id: str) -> list[TaskSpec]:
    report = synthetic_report_from_loop_gaps("loop", gap_pairs)
    return GapTaskCompiler().compile(report, workspace_id)


def taskspecs_to_code_path_jobs(specs: list[TaskSpec]) -> list[dict]:
    """Minimal job dicts for code_path_runner / mission queue."""
    jobs = []
    for s in specs:
        jobs.append(
            {
                "job_id": s.task_id,
                "objective": s.objective,
                "target": s.target,
                "workspace_id": s.workspace_id,
                "acceptance": list(s.acceptance),
                "gap_id": s.gap_id,
                "pipeline": "code_path",
            }
        )
    return jobs
