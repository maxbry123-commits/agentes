from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaiwes_coda_bus_v8 as v8

SCHEMA = "yaiwes.coda.hybrid/v9"
SUBAGENT_CAPABLE = (1, 4, 9, 12, 16, 19, 20, 23)
SERVICE_STAGES = (2, 3, 5, 6, 7, 8, 10, 11, 13, 14, 15, 17, 18, 21, 22, 24)

COMPONENT_MODES: dict[int, str] = {
    1: "subagent",
    2: "state_service",
    3: "planner_gate",
    4: "subagent",
    5: "task_service",
    6: "persistence_service",
    7: "mcp_connection_service",
    8: "coordination_service",
    9: "subagent",
    10: "deterministic_planner",
    11: "memory_service",
    12: "subagent",
    13: "audit_service",
    14: "local_adapter",
    15: "memory_learning_service",
    16: "subagent",
    17: "model_gateway",
    18: "control_plane",
    19: "subagent",
    20: "subagent",
    21: "dag_planner",
    22: "state_hygiene_service",
    23: "subagent",
    24: "finalizer",
}

_ESCALATION_STATUSES = {"BLOCKED", "FAILED", "UNRESOLVED", "LOW_CONFIDENCE", "NO_PROGRESS", "CONFLICT"}


def _verified_metrics(item: dict[str, Any]) -> tuple[int, ...]:
    """Return a deterministic quality vector for one same-problem candidate.

    This never uses an LLM vote. A candidate is rewarded only for durable,
    auditable properties already emitted by V8. Failed or incomplete branches
    cannot outrank a fully closed 24-CODA branch.
    """
    report = item.get("report") if isinstance(item.get("report"), dict) else {}
    evidence = report.get("evidence") if isinstance(report.get("evidence"), list) else []
    research_executed = sum(
        1 for row in evidence
        if isinstance(row, dict) and row.get("research_status") == "EXECUTED"
    )
    workflows_completed = sum(
        1 for row in evidence
        if isinstance(row, dict)
        and isinstance(row.get("internal_state"), dict)
        and row["internal_state"].get("workflow_status") == "COMPLETED"
    )
    status = str(report.get("status", ""))
    return (
        int(item.get("status") == "COMPLETED"),
        int(status.startswith("CLOSED_24_CODA")),
        int(report.get("universal_plug_after_component_24") is True),
        int(report.get("components", 0) == 24),
        int(report.get("completed_internal_workflows", 0) == 24),
        int(report.get("real_internal_workflows_executed", 0) == 24),
        int(report.get("research_cycles", 0) == 24),
        research_executed,
        workflows_completed,
        len(evidence),
    )


def escalation_decision(result: dict[str, Any]) -> dict[str, Any]:
    """Decide, without an LLM vote, whether a normal queue result needs hive help."""
    status = str(result.get("status", "")).upper()
    report = result.get("report") if isinstance(result.get("report"), dict) else {}
    reasons: list[str] = []

    if status in _ESCALATION_STATUSES:
        reasons.append(f"status:{status}")
    if report:
        if int(report.get("components", 0) or 0) not in {0, 24}:
            reasons.append("incomplete_component_chain")
        if int(report.get("research_cycles", 0) or 0) not in {0, 24}:
            reasons.append("incomplete_research_cycle")
        if report.get("universal_plug_after_component_24") is False:
            reasons.append("universal_plug_missing")
    if result.get("no_progress") is True:
        reasons.append("no_progress")
    if result.get("conflict") is True:
        reasons.append("conflicting_evidence")

    return {
        "schema": SCHEMA,
        "escalate": bool(reasons),
        "reasons": sorted(set(reasons)),
        "candidate_components": list(SUBAGENT_CAPABLE) if reasons else [],
        "policy": "structured-state-only",
    }


def deterministic_fan_in(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Select the best verified candidate with a stable lexical tie-break.

    Intended only for branches solving the SAME problem by different safe
    strategies. Independent tasks must use run_independent_queue() instead.
    """
    rows = [dict(row) for row in results]
    if not rows:
        return {"schema": SCHEMA, "status": "UNRESOLVED", "winner": None, "ranked": []}

    ranked = []
    for row in rows:
        candidate_id = str(row.get("candidate_id") or row.get("task_id") or "")
        if not candidate_id:
            raise ValueError("candidate result missing candidate_id/task_id")
        ranked.append({
            "candidate_id": candidate_id,
            "task_id": str(row.get("task_id", candidate_id)),
            "quality": list(_verified_metrics(row)),
            "status": row.get("status"),
        })

    # Highest quality wins. Lexicographically smallest candidate_id breaks exact
    # ties so replaying the same evidence always produces the same winner.
    best_quality = max(tuple(x["quality"]) for x in ranked)
    tied = sorted(
        (x for x in ranked if tuple(x["quality"]) == best_quality),
        key=lambda x: x["candidate_id"],
    )
    winner = tied[0]

    fully_verified = best_quality[:7] == (1, 1, 1, 1, 1, 1, 1)
    ranked.sort(key=lambda x: (tuple(-n for n in x["quality"]), x["candidate_id"]))
    return {
        "schema": SCHEMA,
        "status": "RESOLVED_VERIFIED" if fully_verified else "UNRESOLVED",
        "winner": winner if fully_verified else None,
        "ranked": ranked,
        "selection_policy": "durable-evidence-vector-then-lexical-id",
    }


def run_hive_candidates(
    state_root: str | Path,
    problem_id: str,
    candidates: Iterable[dict[str, Any]],
    *,
    broker: Any = None,
    max_workers: int = 4,
    durable: Any = None,
) -> dict[str, Any]:
    """Fan out same-problem candidates through V8 and deterministically fan in."""
    candidate_rows = [dict(x) for x in candidates]
    if len(candidate_rows) < 2:
        raise ValueError("hive mode requires at least two candidate strategies")
    if not 1 <= int(max_workers) <= 24:
        raise ValueError("max_workers must be 1..24")

    seen: set[str] = set()
    prepared: list[dict[str, Any]] = []
    task_to_candidate: dict[str, str] = {}
    safe_problem = v8.v7._safe_id(problem_id)
    for index, row in enumerate(candidate_rows, 1):
        candidate_id = str(row.pop("candidate_id", f"candidate-{index}"))
        if not candidate_id or candidate_id in seen:
            raise ValueError(f"duplicate/empty candidate_id: {candidate_id!r}")
        seen.add(candidate_id)
        safe_candidate = v8.v7._safe_id(candidate_id)
        task_id = f"{safe_problem}--{safe_candidate}"
        row["problem_id"] = problem_id
        row["candidate_id"] = candidate_id
        row["task_id"] = task_id
        task_to_candidate[task_id] = candidate_id
        prepared.append(row)

    parallel = v8.run_parallel_tasks(
        state_root,
        prepared,
        broker=broker,
        max_workers=max_workers,
        durable=durable,
    )
    candidate_results = []
    for result in parallel.get("results", []):
        row = dict(result)
        row["candidate_id"] = task_to_candidate.get(
            str(row.get("task_id")), str(row.get("task_id", ""))
        )
        candidate_results.append(row)

    fan_in = deterministic_fan_in(candidate_results)
    report = {
        "schema": SCHEMA,
        "mode": "HIVE_CANDIDATES",
        "problem_id": problem_id,
        "candidate_count": len(prepared),
        "parallel_status": parallel.get("status"),
        "durable_queue": parallel.get("durable_queue") is True,
        "fan_in": fan_in,
        "results": candidate_results,
    }
    root = Path(state_root)
    v8.core._atomic_write(root / "HIVE-REPORT-V9.json", report)
    return report


def run_independent_queue(
    state_root: str | Path,
    tasks: Iterable[dict[str, Any]],
    *,
    broker: Any = None,
    max_workers: int = 4,
    durable: Any = None,
) -> dict[str, Any]:
    """Run independent jobs in parallel; deliberately does not choose a winner."""
    if not 1 <= int(max_workers) <= 24:
        raise ValueError("max_workers must be 1..24")
    report = v8.run_parallel_tasks(
        state_root,
        tasks,
        broker=broker,
        max_workers=max_workers,
        durable=durable,
    )
    return {
        "schema": SCHEMA,
        "mode": "INDEPENDENT_QUEUE",
        "status": report.get("status"),
        "durable_queue": report.get("durable_queue") is True,
        "results": report.get("results", []),
        "winner": None,
    }


def activation_contract() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "linear_entrypoint": "yaiwes_coda_bus_v8.run_coda_chain",
        "parallel_entrypoint": "yaiwes_coda_hybrid_v9.run_independent_queue",
        "hive_entrypoint": "yaiwes_coda_hybrid_v9.run_hive_candidates",
        "escalation_entrypoint": "yaiwes_coda_hybrid_v9.escalation_decision",
        "component_order": list(range(1, 25)),
        "component_modes": {str(k): v for k, v in COMPONENT_MODES.items()},
        "subagent_capable": list(SUBAGENT_CAPABLE),
        "service_stages": list(SERVICE_STAGES),
        "research_each_coda": True,
        "durable_queue": True,
        "parallel_workers_bounded": True,
        "deterministic_fan_in": True,
        "universal_plug_after_24": True,
        "external_connections": ["MCP", "API"],
        "unknown_plugin_execution": False,
    }
