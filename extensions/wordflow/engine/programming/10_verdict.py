# -*- coding: utf-8 -*-
"""Process 10 — Checklist pass from pre_gate (input to closure)."""
from __future__ import annotations

from typing import Any


def checklist_passed_from_pre(
    *,
    pre_gate_result: dict[str, Any] | None,
    require_checklist: bool,
    env_prof: str,
) -> bool:
    checklist_passed = True
    if pre_gate_result is not None:
        cl = pre_gate_result.get("checklist")
        if require_checklist or env_prof == "prod":
            checklist_passed = bool(cl and cl.get("passed")) if cl is not None else False
        elif cl is not None:
            checklist_passed = bool(cl.get("passed", True))
    return checklist_passed
