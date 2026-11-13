# -*- coding: utf-8 -*-
"""GoalsCompiler — T0d. Compile Goals OUT from resolved Q-form only. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .structured_questions import resolve_gate

Q_TO_G = {
    "Q01_objective": "G01_objective",
    "Q02_expected_result": "G02_expected_result",
    "Q03_constraints": "G03_constraints",
    "Q04_forbidden": "G04_forbidden",
    "Q05_success_criteria": "G05_success_criteria",
    "Q06_rollback": "G06_rollback",
    "Q07_resources_existing": "G07_resources_existing",
    "Q08_resources_missing": "G08_resources_missing",
    "Q09_engines_allowed": "G09_engines_allowed",
    "Q10_risk_level": "G10_risk_level",
    "Q11_budget": "G11_budget",
    "Q12_approver": "G12_approver",
}

LIST_GOALS = {
    "G03_constraints",
    "G04_forbidden",
    "G07_resources_existing",
    "G08_resources_missing",
    "G09_engines_allowed",
}


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _as_obj(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def compile_goals(form: dict[str, Any], *,
                  goals_id: str | None = None) -> dict[str, Any]:
    """Compile goals only if resolve_gate PASS. Else BLOCKED."""
    gate = resolve_gate(form)
    contract_id = form.get("contract_id") or "unknown"
    form_hash = form.get("form_hash")

    if not gate["ok"]:
        empty_goals = {
            "G01_objective": "",
            "G02_expected_result": "",
            "G03_constraints": [],
            "G04_forbidden": [],
            "G05_success_criteria": "",
            "G06_rollback": "",
            "G07_resources_existing": [],
            "G08_resources_missing": [],
            "G09_engines_allowed": [],
            "G10_risk_level": "unknown",
            "G11_budget": {},
            "G12_approver": "unknown",
        }
        body = {
            "schema_version": "1.0",
            "goals_id": goals_id or f"goals_{uuid.uuid4().hex[:12]}",
            "contract_id": contract_id,
            "form_hash": form_hash,
            "status": "BLOCKED_UNRESOLVED_FORM",
            "goals": empty_goals,
            "source_answers": dict(form.get("answers") or {}),
            "pending": list(gate.get("pending") or []),
        }
        body["goals_hash"] = _hash({k: v for k, v in body.items() if k != "goals_hash"})
        return body

    answers = form.get("answers") or {}
    questions = form.get("questions") or {}

    def val(qid: str) -> Any:
        if qid in answers:
            return answers[qid]
        q = questions.get(qid) or {}
        return q.get("value")

    goals = {
        "G01_objective": _as_str(val("Q01_objective")),
        "G02_expected_result": _as_str(val("Q02_expected_result")),
        "G03_constraints": _as_list(val("Q03_constraints")),
        "G04_forbidden": _as_list(val("Q04_forbidden")),
        "G05_success_criteria": _as_str(val("Q05_success_criteria")),
        "G06_rollback": _as_str(val("Q06_rollback")),
        "G07_resources_existing": _as_list(val("Q07_resources_existing")),
        "G08_resources_missing": _as_list(val("Q08_resources_missing")),
        "G09_engines_allowed": _as_list(val("Q09_engines_allowed")),
        "G10_risk_level": _as_str(val("Q10_risk_level")) or "unknown",
        "G11_budget": _as_obj(val("Q11_budget")),
        "G12_approver": _as_str(val("Q12_approver")) or "unknown",
    }
    if goals["G10_risk_level"] not in ("low", "medium", "high", "unknown"):
        goals["G10_risk_level"] = "unknown"
    if goals["G12_approver"] not in ("auto", "council", "director", "unknown"):
        goals["G12_approver"] = "unknown"

    body = {
        "schema_version": "1.0",
        "goals_id": goals_id or f"goals_{uuid.uuid4().hex[:12]}",
        "contract_id": contract_id,
        "form_hash": form_hash,
        "status": "COMPILED",
        "goals": goals,
        "source_answers": dict(answers),
    }
    body["goals_hash"] = _hash({k: v for k, v in body.items() if k != "goals_hash"})
    return body
