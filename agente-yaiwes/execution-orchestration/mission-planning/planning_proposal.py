# -*- coding: utf-8 -*-
"""PlanningProposal — T0n. Merge to Q as PROPOSED only. No auto-resolve. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

ALLOWED_Q = {
    "Q01_objective",
    "Q02_expected_result",
    "Q03_constraints",
    "Q04_forbidden",
    "Q05_success_criteria",
    "Q06_rollback",
    "Q07_resources_existing",
    "Q08_resources_missing",
    "Q09_engines_allowed",
    "Q10_risk_level",
    "Q11_budget",
    "Q12_approver",
}

ENGINE_IDS = frozenset({"openclaw", "hermes", "both", "fake", "unknown"})


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_proposal(
    contract_id: str,
    *,
    engine_id: str = "fake",
    proposed_answers: dict[str, Any] | None = None,
    task_breakdown: list[dict[str, Any]] | None = None,
    confidence: float = 0.5,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    if engine_id not in ENGINE_IDS:
        raise ValueError(f"invalid engine_id={engine_id}")
    if confidence < 0 or confidence > 1:
        raise ValueError("confidence 0..1")

    answers = {}
    for k, v in (proposed_answers or {}).items():
        if k in ALLOWED_Q:
            answers[k] = v

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "proposal_id": f"pp_{uuid.uuid4().hex[:12]}",
        "contract_id": contract_id or "",
        "engine_id": engine_id,
        "status": "PROPOSAL",
        "proposed_answers": answers,
        "task_breakdown": list(task_breakdown or []),
        "confidence": confidence,
        "evidence_refs": list(evidence_refs or []),
    }
    body["proposal_hash"] = _hash({k: v for k, v in body.items() if k != "proposal_hash"})
    return body


def merge_proposal_into_form(
    form: dict[str, Any],
    proposal: dict[str, Any],
    *,
    auto_accept: bool = False,
    auto_accept_required: bool = False,
) -> dict[str, Any]:
    """Apply proposal to form.

    Default auto_accept=False: only mark questions with status PROPOSED (not ANSWERED).
    If auto_accept=True: non-required OPEN questions become ANSWERED; required only if
    auto_accept_required=True (still default False for safety).
    Never sets form resolved unless all required are ANSWERED after merge.
    """
    if proposal.get("status") != "PROPOSAL":
        raise ValueError("only PROPOSAL status accepted")

    from .structured_questions import answer  # local to avoid cycles at import

    questions = {k: dict(v) for k, v in (form.get("questions") or {}).items()}
    answers = dict(form.get("answers") or {})
    proposed_meta = dict(form.get("proposed") or {})

    for qid, value in (proposal.get("proposed_answers") or {}).items():
        if qid not in questions:
            continue
        q = questions[qid]
        if auto_accept:
            if q.get("required") and not auto_accept_required:
                proposed_meta[qid] = {
                    "value": value,
                    "from_proposal": proposal.get("proposal_id"),
                    "engine_id": proposal.get("engine_id"),
                }
                q["status"] = "PROPOSED" if q.get("status") == "OPEN" else q["status"]
                questions[qid] = q
                continue
            # accept into ANSWERED via answer()
            tmp = {
                "schema_version": form["schema_version"],
                "contract_id": form["contract_id"],
                "questions": questions,
                "answers": answers,
                "required_ids": list(form.get("required_ids") or []),
                "pending": [],
                "resolved": False,
            }
            tmp = answer(tmp, qid, value)
            questions = tmp["questions"]
            answers = tmp["answers"]
        else:
            proposed_meta[qid] = {
                "value": value,
                "from_proposal": proposal.get("proposal_id"),
                "engine_id": proposal.get("engine_id"),
            }
            if q.get("status") == "OPEN":
                q["status"] = "PROPOSED"
                q["value"] = value
                questions[qid] = q

    pending = [
        sid
        for sid, spec in questions.items()
        if spec.get("required") and spec.get("status") != "ANSWERED"
    ]
    out = {
        "schema_version": "1.0",
        "contract_id": form.get("contract_id"),
        "questions": questions,
        "answers": answers,
        "required_ids": list(form.get("required_ids") or []),
        "pending": pending,
        "resolved": len(pending) == 0,
        "proposed": proposed_meta,
        "last_proposal_id": proposal.get("proposal_id"),
    }
    # form_hash optional recompute left to caller via structured_questions if needed
    return out


def accept_proposed(
    form: dict[str, Any],
    question_id: str,
) -> dict[str, Any]:
    """Director accepts one PROPOSED value → ANSWERED."""
    from .structured_questions import answer

    proposed = (form.get("proposed") or {}).get(question_id)
    if not proposed:
        q = (form.get("questions") or {}).get(question_id) or {}
        if q.get("status") != "PROPOSED":
            raise KeyError(f"no proposed value for {question_id}")
        value = q.get("value")
    else:
        value = proposed["value"]
    return answer(form, question_id, value)
