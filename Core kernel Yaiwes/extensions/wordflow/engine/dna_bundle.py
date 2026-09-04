# -*- coding: utf-8 -*-
"""C-30 dna_bundle — package DNA + graph + handoff for remote reconstruct. 0% LLM."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .workflow_dna import compile_dna, verify_dna


class DNABundleError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def build_dna_bundle(
    *,
    lock: dict[str, Any],
    task_graph: dict[str, Any] | None = None,
    policies: dict[str, Any] | None = None,
    resources: dict[str, Any] | None = None,
    workflow_version: str = "1.0",
) -> dict[str, Any]:
    if not isinstance(lock, dict) or not lock.get("lock_id"):
        raise DNABundleError("LOCK_REQUIRED")

    dag_digest = None
    if task_graph and task_graph.get("graph_hash"):
        dag_digest = task_graph["graph_hash"]
    elif task_graph:
        dag_digest = hashlib.sha256(
            json.dumps(task_graph, sort_keys=True, default=str).encode()
        ).hexdigest()

    dna = compile_dna(
        lock,
        workflow_version=workflow_version,
        dag_digest=dag_digest,
        policies=policies,
        objectives=list((lock.get("goals_in") or {}).get("covered_ids") or []),
    )
    v = verify_dna(dna)
    if not v.get("ok"):
        raise DNABundleError("DNA_INVALID", v.get("reason", ""))

    bundle = {
        "schema_version": "1.0",
        "dna": dna,
        "task_graph": dict(task_graph or {}),
        "resources": dict(resources or {}),
        "handoff": {
            "lock_id": lock.get("lock_id"),
            "dna_id": dna.get("dna_id"),
            "dna_hash": dna.get("dna_hash"),
            "graph_id": (task_graph or {}).get("graph_id"),
        },
        "llm_control": "DENY",
    }
    bundle["bundle_hash"] = hashlib.sha256(
        json.dumps(
            {k: v for k, v in bundle.items() if k != "bundle_hash"},
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()
    return {"ok": True, "bundle": bundle}
