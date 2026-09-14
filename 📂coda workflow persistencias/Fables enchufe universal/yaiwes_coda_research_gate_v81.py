from __future__ import annotations

from typing import Any, Iterable

import yaiwes_coda_bus_v8 as bus_v8
import yaiwes_coda_research_gate_v71 as gate_v71

SCHEMA = "yaiwes.coda.research-gate/v8.1"


def build_research_broker():
    """Reuse the audited V7.1 API/MCP research broker without a second engine."""
    return gate_v71.build_research_broker()


def _validate_chain_report(report: dict[str, Any]) -> None:
    if report.get("components") != 24:
        raise RuntimeError("canonical CODA chain must contain 24 components")
    if report.get("real_internal_workflows_executed") != 24:
        raise RuntimeError("all 24 real internal workflows must execute")
    if report.get("research_cycles") != 24:
        raise RuntimeError("all 24 CODA research cycles are required")
    evidence = report.get("evidence") or []
    if len(evidence) != 24:
        raise RuntimeError("24 CODA evidence records are required")
    if any(item.get("research_status") != "EXECUTED" for item in evidence):
        raise RuntimeError("a CODA research cycle did not execute")
    if not report.get("universal_plug_after_component_24"):
        raise RuntimeError("universal plug must receive only after component 24")


def run_coda_chain(
    state_root,
    task_id: str,
    task: dict[str, Any] | None = None,
    *,
    durable=None,
) -> dict[str, Any]:
    """Durable V8 chain with fail-closed real research on every CODA."""
    broker = build_research_broker()
    report = bus_v8.run_coda_chain(
        state_root,
        task_id,
        task,
        broker=broker,
        durable=durable,
    )
    _validate_chain_report(report)
    return {
        **report,
        "research_gate_schema": SCHEMA,
        "research_fail_closed": True,
    }


def run_parallel_tasks(
    state_root,
    tasks: Iterable[dict[str, Any]],
    *,
    max_workers: int = 4,
    durable=None,
) -> dict[str, Any]:
    """Durable fan-out; every branch still requires 24 real research cycles."""
    broker = build_research_broker()
    report = bus_v8.run_parallel_tasks(
        state_root,
        tasks,
        broker=broker,
        max_workers=max_workers,
        durable=durable,
    )
    if report.get("status") != "COMPLETED":
        raise RuntimeError("parallel CODA execution did not complete")
    for result in report.get("results", []):
        if result.get("status") != "COMPLETED" or not isinstance(result.get("report"), dict):
            raise RuntimeError("parallel branch did not complete")
        _validate_chain_report(result["report"])
    return {
        **report,
        "research_gate_schema": SCHEMA,
        "research_fail_closed": True,
    }
