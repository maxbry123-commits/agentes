# -*- coding: utf-8 -*-
"""loop_bridge — G2. InputContract → Questions → Goals → GoalLock. 0% LLM.

Canonical entry for main_loop / facade. Does not call engines.
"""
from __future__ import annotations

from typing import Any

from .goal_lock import create_goal_lock, verify_lock_integrity
from .goals_compiler import compile_goals
from .input_compiler import compile_input_contract
from .structured_questions import answer, build_from_contract, resolve_gate


def bridge_to_lock(
    raw_input: str,
    *,
    auto_answer_approver: str | None = "director",
    require_resolved: bool = True,
) -> dict[str, Any]:
    """Compile raw text to GoalLock via canonical InputContract path.

    If auto_answer_approver is set, answers Q12_approver only (deterministic test/bootstrap).
    Production should pass answers explicitly via bridge_with_answers.
    """
    contract = compile_input_contract(raw_input)
    form = build_from_contract(contract)
    if auto_answer_approver:
        form = answer(form, "Q12_approver", auto_answer_approver)
    gate = resolve_gate(form)
    if require_resolved and not gate.get("ok"):
        return {
            "ok": False,
            "stage": "questions",
            "gate": gate,
            "contract": contract,
            "form": form,
        }
    goals = compile_goals(form)
    lock = create_goal_lock(goals)
    integ = verify_lock_integrity(lock)
    if not integ.get("ok"):
        return {"ok": False, "stage": "lock", "integrity": integ, "goals": goals}
    return {
        "ok": True,
        "stage": "lock",
        "contract": contract,
        "form": form,
        "goals": goals,
        "lock": lock,
        "gate": gate,
    }


def bridge_with_answers(
    raw_input: str,
    answers: dict[str, str],
    *,
    require_resolved: bool = True,
) -> dict[str, Any]:
    """Same as bridge_to_lock but apply explicit Q* answers (no silent defaults beyond given)."""
    contract = compile_input_contract(raw_input)
    form = build_from_contract(contract)
    for qid, val in (answers or {}).items():
        form = answer(form, qid, val)
    gate = resolve_gate(form)
    if require_resolved and not gate.get("ok"):
        return {
            "ok": False,
            "stage": "questions",
            "gate": gate,
            "contract": contract,
            "form": form,
        }
    goals = compile_goals(form)
    lock = create_goal_lock(goals)
    integ = verify_lock_integrity(lock)
    if not integ.get("ok"):
        return {"ok": False, "stage": "lock", "integrity": integ}
    return {
        "ok": True,
        "stage": "lock",
        "contract": contract,
        "form": form,
        "goals": goals,
        "lock": lock,
        "gate": gate,
    }
