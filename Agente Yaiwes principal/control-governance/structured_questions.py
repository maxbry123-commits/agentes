# -*- coding: utf-8 -*-
"""StructuredQuestionsEngine — T0b. Q01-Q12 fixed form + resolve gate. 0% LLM."""
from __future__ import annotations

import hashlib
import json
from typing import Any

QUESTION_SPECS: list[dict[str, Any]] = [
    {"id": "Q01_objective", "prompt": "Single primary objective (one action)", "value_type": "string", "required": True},
    {"id": "Q02_expected_result", "prompt": "Expected result / deliverable", "value_type": "string", "required": False},
    {"id": "Q03_constraints", "prompt": "Constraints list", "value_type": "list", "required": False},
    {"id": "Q04_forbidden", "prompt": "Forbidden actions list", "value_type": "list", "required": False},
    {"id": "Q05_success_criteria", "prompt": "Success criteria (executable or observable)", "value_type": "string", "required": True},
    {"id": "Q06_rollback", "prompt": "Rollback command or procedure", "value_type": "string", "required": False},
    {"id": "Q07_resources_existing", "prompt": "Resources already available", "value_type": "list", "required": False},
    {"id": "Q08_resources_missing", "prompt": "Resources still missing", "value_type": "list", "required": False},
    {"id": "Q09_engines_allowed", "prompt": "Engines allowed for this task", "value_type": "list", "required": False},
    {
        "id": "Q10_risk_level",
        "prompt": "Risk level",
        "value_type": "enum",
        "required": True,
        "enum_values": ["low", "medium", "high", "unknown"],
    },
    {"id": "Q11_budget", "prompt": "Budget tokens/time_s/cost", "value_type": "object", "required": False},
    {
        "id": "Q12_approver",
        "prompt": "Approver",
        "value_type": "enum",
        "required": True,
        "enum_values": ["auto", "council", "director", "unknown"],
    },
]

CONTRACT_TO_Q = {
    "objective": "Q01_objective",
    "expected_result": "Q02_expected_result",
    "constraints": "Q03_constraints",
    "forbidden": "Q04_forbidden",
    "success_criteria": "Q05_success_criteria",
    "rollback": "Q06_rollback",
    "resources_declared": "Q07_resources_existing",
    "engines_allowed": "Q09_engines_allowed",
    "risk_level": "Q10_risk_level",
    "budget": "Q11_budget",
    "approver": "Q12_approver",
}


def _filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _hash_form(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_from_contract(contract: dict[str, Any]) -> dict[str, Any]:
    """Seed Q01-Q12 from InputContract. Mark ANSWERED when value present."""
    if not isinstance(contract, dict):
        raise ValueError("contract must be dict")
    contract_id = contract.get("contract_id") or "unknown"

    questions: dict[str, Any] = {}
    answers: dict[str, Any] = {}
    pending: list[str] = []
    required_ids: list[str] = []

    seed_map = {
        "Q01_objective": contract.get("objective"),
        "Q02_expected_result": contract.get("expected_result"),
        "Q03_constraints": contract.get("constraints") or [],
        "Q04_forbidden": contract.get("forbidden") or [],
        "Q05_success_criteria": contract.get("success_criteria"),
        "Q06_rollback": contract.get("rollback"),
        "Q07_resources_existing": contract.get("resources_declared") or [],
        "Q08_resources_missing": [],
        "Q09_engines_allowed": contract.get("engines_allowed") or [],
        "Q10_risk_level": contract.get("risk_level") or "unknown",
        "Q11_budget": contract.get("budget") or {},
        "Q12_approver": contract.get("approver") or "unknown",
    }

    for spec in QUESTION_SPECS:
        qid = spec["id"]
        if spec["required"]:
            required_ids.append(qid)
        value = seed_map.get(qid)
        answered = _filled(value)
        # unknown enums count as not answered for required risk/approver if still unknown and required planning
        if qid in ("Q10_risk_level", "Q12_approver") and value == "unknown" and spec["required"]:
            # risk unknown is acceptable seed; approver unknown keeps OPEN for gate if policy wants explicit
            answered = qid == "Q10_risk_level"
        status = "ANSWERED" if answered else "OPEN"
        q: dict[str, Any] = {
            "id": qid,
            "prompt": spec["prompt"],
            "value_type": spec["value_type"],
            "required": spec["required"],
            "status": status,
            "value": value if answered else None,
        }
        if "enum_values" in spec:
            q["enum_values"] = list(spec["enum_values"])
        questions[qid] = q
        if answered:
            answers[qid] = value
        elif spec["required"]:
            pending.append(qid)

    body = {
        "schema_version": "1.0",
        "contract_id": contract_id,
        "questions": questions,
        "answers": answers,
        "required_ids": required_ids,
        "pending": pending,
        "resolved": len(pending) == 0,
    }
    body["form_hash"] = _hash_form({k: v for k, v in body.items() if k != "form_hash"})
    return body


def answer(form: dict[str, Any], question_id: str, value: Any) -> dict[str, Any]:
    """Set one answer. Recompute pending/resolved."""
    if question_id not in form.get("questions", {}):
        raise KeyError(f"unknown question_id={question_id}")
    q = dict(form["questions"][question_id])
    if q["value_type"] == "enum" and q.get("enum_values") and value not in q["enum_values"]:
        raise ValueError(f"invalid enum value for {question_id}: {value}")
    if q["value_type"] == "list" and not isinstance(value, list):
        raise ValueError(f"{question_id} expects list")
    if q["value_type"] == "object" and not isinstance(value, dict):
        raise ValueError(f"{question_id} expects object")
    if q["value_type"] == "string" and not isinstance(value, str):
        raise ValueError(f"{question_id} expects string")

    q["value"] = value
    q["status"] = "ANSWERED" if _filled(value) else "OPEN"
    questions = dict(form["questions"])
    questions[question_id] = q
    answers = dict(form.get("answers") or {})
    if q["status"] == "ANSWERED":
        answers[question_id] = value
    else:
        answers.pop(question_id, None)

    pending = [
        sid
        for sid, spec in questions.items()
        if spec["required"] and spec["status"] != "ANSWERED"
    ]
    body = {
        "schema_version": "1.0",
        "contract_id": form["contract_id"],
        "questions": questions,
        "answers": answers,
        "required_ids": list(form.get("required_ids") or []),
        "pending": pending,
        "resolved": len(pending) == 0,
    }
    body["form_hash"] = _hash_form({k: v for k, v in body.items() if k != "form_hash"})
    return body


def resolve_gate(form: dict[str, Any]) -> dict[str, Any]:
    """Gate: PASS only if all required questions ANSWERED."""
    pending = list(form.get("pending") or [])
    resolved = bool(form.get("resolved")) and len(pending) == 0
    return {
        "ok": resolved,
        "resolved": resolved,
        "pending": pending,
        "contract_id": form.get("contract_id"),
        "form_hash": form.get("form_hash"),
        "reason": "RESOLVED" if resolved else "PENDING_REQUIRED_QUESTIONS",
    }
