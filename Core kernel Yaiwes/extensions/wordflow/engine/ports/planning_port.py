# -*- coding: utf-8 -*-
"""PlanningPort — T0o. Interface + Fake engines. No network. 0% LLM."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..planning_proposal import make_proposal


@runtime_checkable
class PlanningPort(Protocol):
    """Port for planning engines. Real adapters post-Wordflow (T3)."""

    engine_id: str

    def propose(self, contract: dict[str, Any], form: dict[str, Any]) -> dict[str, Any]:
        """Return PlanningProposal (status=PROPOSAL)."""
        ...


class FakeOpenClawPlanner:
    """Deterministic fake — extracts gaps from form pending."""

    engine_id = "openclaw"

    def propose(self, contract: dict[str, Any], form: dict[str, Any]) -> dict[str, Any]:
        pending = list(form.get("pending") or [])
        proposed: dict[str, Any] = {}
        if "Q01_objective" in pending:
            raw = (contract.get("raw_literal") or "")[:120]
            proposed["Q01_objective"] = f"[fake-openclaw] plan: {raw or 'objective pendiente'}"
        if "Q05_success_criteria" in pending:
            proposed["Q05_success_criteria"] = "[fake-openclaw] tests PASS + commit"
        if "Q12_approver" in pending:
            proposed["Q12_approver"] = "director"
        breakdown = [
            {"id": "t1", "title": "resolver form pendiente", "depends_on": []},
            {"id": "t2", "title": "compilar goals", "depends_on": ["t1"]},
        ]
        return make_proposal(
            contract.get("contract_id") or form.get("contract_id") or "",
            engine_id="openclaw",
            proposed_answers=proposed,
            task_breakdown=breakdown,
            confidence=0.6,
            evidence_refs=["fake_openclaw_v1"],
        )


class FakeHermesPlanner:
    """Deterministic fake — memory-flavored constraints proposals."""

    engine_id = "hermes"

    def propose(self, contract: dict[str, Any], form: dict[str, Any]) -> dict[str, Any]:
        proposed: dict[str, Any] = {}
        pending = list(form.get("pending") or [])
        answers = form.get("answers") or {}
        if "Q03_constraints" in pending or not answers.get("Q03_constraints"):
            proposed["Q03_constraints"] = ["0% LLM en core", "no bypass GoalLock"]
        if "Q04_forbidden" in pending or not answers.get("Q04_forbidden"):
            proposed["Q04_forbidden"] = ["reescribir lock", "auto_accept required"]
        if "Q12_approver" in pending:
            proposed["Q12_approver"] = "director"
        return make_proposal(
            contract.get("contract_id") or form.get("contract_id") or "",
            engine_id="hermes",
            proposed_answers=proposed,
            task_breakdown=[
                {"id": "m1", "title": "inyectar constraints memoria", "depends_on": []},
            ],
            confidence=0.55,
            evidence_refs=["fake_hermes_v1"],
        )


def run_planning_ports(
    ports: list[PlanningPort],
    contract: dict[str, Any],
    form: dict[str, Any],
) -> list[dict[str, Any]]:
    """Call each port; collect proposals. No merge (caller uses planning_proposal.merge)."""
    out: list[dict[str, Any]] = []
    for port in ports:
        prop = port.propose(contract, form)
        if prop.get("status") != "PROPOSAL":
            raise ValueError(f"port {getattr(port, 'engine_id', '?')} non-PROPOSAL")
        out.append(prop)
    return out
