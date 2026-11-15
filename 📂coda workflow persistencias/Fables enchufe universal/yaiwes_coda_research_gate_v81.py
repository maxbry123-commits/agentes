from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaiwes_coda_bus_v8 as bus_v8
import yaiwes_coda_research_gate_v71 as gate_v71

SCHEMA = "yaiwes.coda.research-gate/v8.1"


def build_research_broker():
    """Reuse the audited V7.1 API/MCP research broker; do not create a second engine."""
    return gate_v71.build_research_broker()


def _validate_chain_report(report: dict[str, Any]) -> None:
    evidence = report.get("evidence", [])
    if report.get("components") != 24:
        raise RuntimeError("all 24 CODA components are required")
    if report.get("real_internal_workflows_executed") != 24:
        raise RuntimeError("all 24 internal workflows must execute")
    if report.get("research_cycles") != 24 or len(evidence) != 24:
        raise RuntimeError("all 24 CODA research cycles are required")
    if any(item.get("research_status") != "EXECUTED" for item in evidence):
        raise RuntimeError("a CODA research cycle did not execute")
    if report.get("universal_plug_after_component_24") is not True:
        raise RuntimeError("universal plug must run after component 24")


def run_coda_chain(state_root, task_id: str, task: dict[str, Any] | None = None, *, durable=None) -> dict[str, Any]:
    broker = build_research_broker()
    report = bus_v8.run_coda_chain(Path(state_root), task_id, task, broker=broker, durable=durable)
    _validate_chain_report(report)
    return {**report, "research_gate_schema": SCHEMA, "research_fail_closed": True}


def run_parallel_tasks(state_root, tasks: Iterable[dict[str, Any]], *, max_workers: int = 4, durable=None) -> dict[str, Any]:
    broker = build_research_broker()
    report = bus_v8.run_parallel_tasks(Path(state_root), tasks, broker=broker, max_workers=max_workers, durable=durable)
    if report.get("status") != "COMPLETED":
        raise RuntimeError("parallel CODA execution did not complete")
    for branch in report.get("results", []):
        if branch.get("status") != "COMPLETED":
            raise RuntimeError("parallel CODA branch did not complete")
        _validate_chain_report(branch.get("report", {}))
    return {**report, "research_gate_schema": SCHEMA, "research_fail_closed": True}
