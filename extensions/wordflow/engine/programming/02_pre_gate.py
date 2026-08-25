# -*- coding: utf-8 -*-
"""Process 02 — PreGate COPY-FIRST + Sheriff + optional adapt."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def run_pre_gate(
    *,
    require_pre_gate: bool,
    symbol_or_stem: str,
    dest: str,
    dest_resolved: str,
    context_verified: bool,
    handoff_verified: bool,
    checklist: Any,
    require_checklist: bool,
    apply_adapt: bool,
    import_mapping: dict[str, str] | None,
    mission_id: str,
    env_prof: str,
    gap_reg: Any,
    wire_trace: dict[str, Any],
) -> dict[str, Any]:
    """Returns dict with keys: block (optional early return), pre_gate_result, pre_ok, adapted_dest."""
    from extensions.wordflow.standards.executor_gates import ExecutorPreImplementGate
    from extensions.wordflow.standards.gap_registry import Gap
    from extensions.wordflow.standards.copy_first import copy_file_deterministic
    from extensions.wordflow.standards.adapt_imports import adapt_file
    from extensions.wordflow.standards.path_resolve import resolve_path
    from extensions.wordflow.standards.checklist_sheriff import AgentChecklistClaim

    pre_gate_result = None
    pre_ok = False
    adapted_dest = ""
    dest_use = dest_resolved or dest

    if not (require_pre_gate or symbol_or_stem or dest):
        return {"pre_gate_result": None, "pre_ok": False, "adapted_dest": ""}

    if not symbol_or_stem or not dest_use:
        if require_pre_gate:
            return {
                "block": {
                    "ok": False,
                    "stage": "pre_gate",
                    "detail": "BLOCK: need symbol_or_stem + dest",
                    "llm_control": "DENY",
                    "verdict": "BLOCK",
                    "wire_trace": wire_trace,
                }
            }
        return {"pre_gate_result": None, "pre_ok": False, "adapted_dest": ""}

    pre = ExecutorPreImplementGate()
    pre_gate_result = pre.check(
        context_verified=context_verified,
        handoff_verified=handoff_verified,
        symbol_or_stem=symbol_or_stem,
        dest=dest_use,
        checklist=checklist if isinstance(checklist, AgentChecklistClaim) else checklist,
        require_checklist=require_checklist or (env_prof == "prod"),
    )
    wire_trace["pre_gate"] = pre_gate_result
    pre_ok = bool(pre_gate_result.get("allow"))
    if not pre_ok:
        gap_reg.add(Gap(
            gap_id="GC-PRE-001", task_id="C-19", mission_id=mission_id or "",
            rule_id="COPY_FIRST_OR_SHERIFF", severity="blocking",
            description=str(pre_gate_result.get("reason")), location="pre_gate",
        ))
        return {
            "block": {
                "ok": False,
                "stage": "pre_gate",
                "detail": pre_gate_result,
                "llm_control": "DENY",
                "verdict": "BLOCK",
                "gaps": gap_reg.to_list(),
                "wire_trace": wire_trace,
            },
            "pre_gate_result": pre_gate_result,
            "pre_ok": False,
            "adapted_dest": "",
        }

    if apply_adapt and pre_ok:
        cf = pre_gate_result.get("copy_first") or {}
        sources = cf.get("sources") or []
        action = cf.get("action", "")
        if sources and dest_use:
            src = Path(sources[0])
            if not src.exists():
                try:
                    src = resolve_path(sources[0], must_exist=True)
                except Exception:
                    src = Path(sources[0])
            dst = Path(dest_use)
            if src.exists():
                if action in ("ADAPT", "COPY") and import_mapping:
                    rewrites = adapt_file(src, dst, import_mapping)
                    wire_trace["adapt"] = {"action": "ADAPT", "rewrites": rewrites, "src": str(src), "dest": str(dst)}
                else:
                    wire_trace["adapt"] = copy_file_deterministic(src, dst)
                adapted_dest = str(dst)
                try:
                    txt = dst.read_text(encoding="utf-8")
                    import ast
                    ast.parse(txt)
                    wire_trace["post_adapt"] = {"ok": True, "path": str(dst)}
                except Exception as e:
                    wire_trace["post_adapt"] = {"ok": False, "error": str(e)}
                    gap_reg.add(Gap(
                        gap_id="GC-ADAPT-001", task_id="C-19", mission_id=mission_id or "",
                        rule_id="POST_ADAPT", severity="blocking",
                        description=str(e), location=str(dst),
                    ))
                    return {
                        "block": {
                            "ok": False,
                            "stage": "post_adapt",
                            "detail": wire_trace["post_adapt"],
                            "llm_control": "DENY",
                            "verdict": "FAIL",
                            "gaps": gap_reg.to_list(),
                            "wire_trace": wire_trace,
                        },
                        "pre_gate_result": pre_gate_result,
                        "pre_ok": pre_ok,
                        "adapted_dest": adapted_dest,
                    }

    return {"pre_gate_result": pre_gate_result, "pre_ok": pre_ok, "adapted_dest": adapted_dest}
