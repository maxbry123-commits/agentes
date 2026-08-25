# -*- coding: utf-8 -*-
"""Process 01 — Context + handoff gate (BLOCK if missing)."""
from __future__ import annotations
from typing import Any


def run_context_manifest(* , require_context_manifest: bool, context_manifest: Any, wire_trace: dict[str, Any]) -> dict[str, Any] | None:
    if not require_context_manifest:
        return None
    from extensions.wordflow.standards.context_manifest import ContextManifest, ContextValidator
    if context_manifest is None:
        return {"ok": False, "stage": "context_manifest", "detail": "BLOCK: manifest None", "llm_control": "DENY", "verdict": "BLOCK", "wire_trace": wire_trace}
    if isinstance(context_manifest, dict):
        keys = ("mission_id", "task_id", "project_docs", "architecture_docs", "task_spec", "relevant_files", "contracts", "tests", "repository_revision", "handoff_ref")
        context_manifest = ContextManifest(**{k: context_manifest[k] for k in keys if k in context_manifest})
    cv = ContextValidator().validate(context_manifest)
    wire_trace["context_manifest"] = cv
    if not cv.get("ok"):
        return {"ok": False, "stage": "context_manifest", "detail": cv, "llm_control": "DENY", "verdict": "BLOCK", "wire_trace": wire_trace}
    return {"context_verified": True, "handoff_verified": True, "_continue": True}


def run_require_context(* , context_verified: bool, handoff_verified: bool, wire_trace: dict[str, Any]) -> dict[str, Any] | None:
    from extensions.wordflow.standards.verdict_authority import VerdictAuthority
    block = VerdictAuthority().require_context(context_verified, handoff_verified)
    if block:
        return {"ok": False, "stage": "context", "detail": block, "llm_control": "DENY", "verdict": "BLOCK", "wire_trace": wire_trace}
    return None
