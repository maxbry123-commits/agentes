# -*- coding: utf-8 -*-
"""dna_handoff — T42. Handoff package includes WorkflowDNA. 0% LLM."""
from __future__ import annotations

from typing import Any

from .goal_lock import verify_lock_integrity
from .handoff import build_handoff  # type: ignore
from .workflow_dna import compile_dna, verify_dna


def build_dna_handoff(
    lock: dict[str, Any],
    *,
    workflow_version: str = "1.0",
    policies: dict[str, Any] | None = None,
    dag_digest: str | None = None,
    success_criteria: list[Any] | None = None,
    rollback: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    integ = verify_lock_integrity(lock)
    if not integ.get("ok"):
        return {"ok": False, "reason": "LOCK_FAIL", "detail": integ}

    dna = compile_dna(
        lock,
        workflow_version=workflow_version,
        policies=policies,
        dag_digest=dag_digest,
        success_criteria=success_criteria,
        rollback=rollback,
    )
    v = verify_dna(dna)
    if not v.get("ok"):
        return {"ok": False, "reason": "DNA_FAIL", "detail": v}

    # Prefer existing handoff builder if signature matches; else minimal package
    package: dict[str, Any]
    try:
        package = build_handoff(lock=lock, dna=dna, **(extra or {}))  # type: ignore[call-arg]
        if not isinstance(package, dict):
            raise TypeError("handoff not dict")
    except Exception:
        package = {
            "schema_version": "1.0",
            "lock_id": lock.get("lock_id"),
            "dna": dna,
            "payload": dict(extra or {}),
        }

    package["dna"] = dna
    package["dna_id"] = dna["dna_id"]
    package["dna_hash"] = dna["dna_hash"]
    package["ok"] = True
    return package


def accept_dna_handoff(package: dict[str, Any]) -> dict[str, Any]:
    """Remote node: verify DNA before accepting work."""
    if not isinstance(package, dict):
        return {"ok": False, "reason": "INVALID_PACKAGE"}
    dna = package.get("dna")
    if not isinstance(dna, dict):
        return {"ok": False, "reason": "NO_DNA"}
    v = verify_dna(dna)
    if not v.get("ok"):
        return {"ok": False, "reason": "DNA_TAMPER", "detail": v}
    return {
        "ok": True,
        "dna_id": dna.get("dna_id"),
        "lock_id": dna.get("lock_id"),
        "workflow_version": dna.get("workflow_version"),
    }
