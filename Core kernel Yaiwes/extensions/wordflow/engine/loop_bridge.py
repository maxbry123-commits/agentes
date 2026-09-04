# -*- coding: utf-8 -*-
"""loop_bridge — G2/G3. Contract→Lock + echo/registers/classify/ping. 0% LLM."""
from __future__ import annotations

from typing import Any

from .cognitive_registers import load_from_lock
from .goal_lock import create_goal_lock, verify_lock_integrity
from .goals_compiler import compile_goals
from .input_compiler import compile_input_contract
from .objective_echo import inject_echo
from .push_ping import emit_ping
from .structured_questions import answer, build_from_contract, resolve_gate
from .task_classifier import classify_task, decision_gate


def bridge_to_lock(
    raw_input: str,
    *,
    auto_answer_approver: str | None = "director",
    require_resolved: bool = True,
    allow_raw_literal_fallback: bool = False,
) -> dict[str, Any]:
    contract = compile_input_contract(raw_input)
    form = build_from_contract(contract)
    if auto_answer_approver:
        form = answer(form, "Q12_approver", auto_answer_approver)
    gate = resolve_gate(form)

    # Mission entry may explicitly accept the already-validated raw literal as
    # both objective and observable success criterion. Generic bridge callers
    # remain fail-closed unless this opt-in is requested by mission.py.
    if (
        allow_raw_literal_fallback
        and not gate.get("ok")
        and isinstance(contract.get("raw_literal"), str)
        and contract["raw_literal"].strip()
        and set(gate.get("pending") or []) <= {"Q01_objective", "Q05_success_criteria"}
    ):
        literal = contract["raw_literal"].strip()
        contract = dict(contract)
        contract["objective"] = literal
        contract["success_criteria"] = literal
        contract["missing_fields"] = []
        contract["status"] = "COMPLETE"
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


def bridge_full(
    raw_input: str,
    *,
    task_hint: str = "",
    auto_answer_approver: str | None = "director",
    emit_initial_ping: bool = True,
) -> dict[str, Any]:
    """G3: lock + objective echo + registers + task classify + optional ping."""
    base = bridge_to_lock(
        raw_input,
        auto_answer_approver=auto_answer_approver,
        require_resolved=True,
    )
    if not base.get("ok"):
        return base

    lock = base["lock"]
    echo = inject_echo(lock, task_hint or "bridge_full")
    registers = load_from_lock(lock)
    classification = classify_task(
        task_hint or lock.get("objective") or "",
        lock=lock,
    )
    dgate = decision_gate(classification)

    ping = None
    if emit_initial_ping:
        try:
            ping = emit_ping(lock_id=lock.get("lock_id"), reason="bridge_full_start")
        except TypeError:
            try:
                ping = emit_ping(lock)
            except Exception as exc:  # noqa: BLE001
                ping = {"ok": False, "error": str(exc)}

    return {
        **base,
        "ok": bool(dgate.get("ok", True)) if isinstance(dgate, dict) else True,
        "stage": "full",
        "echo": echo,
        "registers": registers,
        "classification": classification,
        "decision_gate": dgate,
        "ping": ping,
    }


def bridge_run_fake(payload: dict) -> dict:
    """T14: runner↔loop bridge with publish Fake. No network."""
    if not isinstance(payload, dict):
        return {
            "status": "error",
            "stages": [],
            "evidence": {"error": "payload must be dict"},
        }
    stages: list[str] = []
    text = str(
        payload.get("text")
        or payload.get("raw")
        or payload.get("goal")
        or "fake"
    )
    stages.append("intake")
    stages.append("code_path_dry")
    stages.append("loop_fake")
    publish = {"ok": True, "mode": "fake", "published": False, "network": False}
    try:
        from .publish_path import publish_after_mission  # noqa: F401

        publish["wired"] = True
    except Exception:
        publish["wired"] = False
    stages.append("publish_fake")
    evidence = {
        "payload_keys": sorted(str(k) for k in payload.keys()),
        "text": text[:80],
        "publish": publish,
        "instance_id": payload.get("instance_id", "v1"),
    }
    return {"status": "ok", "stages": stages, "evidence": evidence}
