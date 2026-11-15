# -*- coding: utf-8 -*-
"""FakeEngine stubs — T4. No network. For RuntimeBus tests. 0% LLM."""
from __future__ import annotations

from typing import Any

from ..engine_abi import make_result
from ..planning_proposal import make_proposal


class StaticFakeEngine:
    """Returns fixed output_text."""

    def __init__(self, engine_id: str = "fake_static", output_text: str = "static-ok"):
        self.engine_id = engine_id
        self.output_text = output_text

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        return make_result(
            job,
            status="OK",
            output_text=self.output_text,
            artifacts=[f"artifact:{self.engine_id}"],
        )


class EchoFakeEngine:
    """Echoes job input.prompt (and optional echo_block prefix)."""

    def __init__(self, engine_id: str = "fake_echo"):
        self.engine_id = engine_id

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        inp = job.get("input") or {}
        prompt = inp.get("prompt") or ""
        echo = inp.get("echo_block") or ""
        text = f"{echo}\n{prompt}".strip() if echo else prompt
        return make_result(job, status="OK", output_text=text)


class PlanningFakeEngine:
    """Returns PlanningProposal JSON-ish text for PLANNING route."""

    def __init__(self, engine_id: str = "fake_planning"):
        self.engine_id = engine_id

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        prop = make_proposal(
            job.get("lock_id") or "",
            engine_id="fake",
            proposed_answers={
                "Q12_approver": "director",
            },
            confidence=0.5,
            evidence_refs=["fake_planning_engine"],
        )
        return make_result(
            job,
            status="OK",
            output_text=str(prop),
            artifacts=[prop.get("proposal_id") or ""],
        )


class ErrorFakeEngine:
    """Always ERROR."""

    def __init__(self, engine_id: str = "fake_error"):
        self.engine_id = engine_id

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        return make_result(
            job,
            status="ERROR",
            error_code="FAKE_ERROR",
            error_detail="intentional",
        )
