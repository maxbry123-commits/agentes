# -*- coding: utf-8 -*-
"""Report builder — E3. Capa1/2/3 → formato auditor CHAT_B. 0% LLM."""
from __future__ import annotations

from typing import Any


def build_report(verdict: dict[str, Any] | None, *,
                 task_id: str | None = None,
                 final_commit: str | None = None) -> dict[str, Any]:
    """Normalize verdict into explicit 3-layer audit report."""
    v = verdict or {}
    veredicto = v.get("veredicto") or "PARCIAL"
    reasons = list(v.get("reason_codes") or [])
    capa1 = dict(v.get("capa1") or {
        "veredicto": veredicto,
        "reason_codes": reasons,
        "completitud_hint": 0,
    })
    capa2 = dict(v.get("capa2") or {})
    capa3 = dict(v.get("capa3") or {})

    return {
        "schema_version": "1.0",
        "task_id": task_id,
        "final_commit": final_commit,
        "veredicto": veredicto,
        "reason_codes": reasons,
        "capa1": capa1,
        "capa2": capa2,
        "capa3": capa3,
        "ci_note": (
            "silence_is_not_pass: tests claimed without ci_run_id → PARCIAL/CI_MISSING"
        ),
    }


def format_capa1_text(report: dict[str, Any]) -> str:
    """Micro resumen texto (Capa 1)."""
    c1 = report.get("capa1") or {}
    codes = ", ".join(report.get("reason_codes") or []) or "—"
    return (
        f"VEREDICTO: {report.get('veredicto')}\n"
        f"COMPLETITUD: {c1.get('completitud_hint', 0)}%\n"
        f"REASON_CODES: {codes}\n"
        f"CI_NOTE: {report.get('ci_note')}\n"
    )
