# -*- coding: utf-8 -*-
"""ResourceTraceBuilder — T0c. Inventory pre-plan. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Default paths relative to repo/workspace that Wordflow cares about pre-plan.
DEFAULT_PROBE_PATHS = [
    "extensions/wordflow",
    "extensions/wordflow/engine",
    "extensions/wordflow/schemas",
    "extensions/wordflow/schemas/input_contract.schema.json",
    "extensions/wordflow/schemas/structured_questions.schema.json",
    "extensions/wordflow/engine/input_compiler.py",
    "extensions/wordflow/engine/structured_questions.py",
    "PIPELINE/29_YAIWES_RUNTIME_GAPS_Y_PLAN.md",
    "PIPELINE/30_KIMI_COGNITIVE_RUNTIME_INTEGRATION.md",
    "extensions/control-layer",
    "extensions/source_evolution",
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _kind_for_path(rel: str) -> str:
    if rel.endswith((".json", ".yaml", ".yml")) and "schema" in rel:
        return "schema"
    if rel.startswith("extensions/"):
        parts = rel.split("/")
        if len(parts) == 2:
            return "extension"
        if rel.endswith(".py"):
            return "file"
        return "path"
    if rel.startswith("PIPELINE/"):
        return "file"
    return "path"


def _probe_path(root: Path, rel: str) -> dict[str, Any]:
    target = root / rel
    exists = target.exists()
    meta: dict[str, Any] = {}
    if exists:
        meta["is_dir"] = target.is_dir()
        if target.is_file():
            try:
                meta["size"] = target.stat().st_size
            except OSError:
                meta["size"] = None
    return {
        "resource_id": f"path:{rel}",
        "kind": _kind_for_path(rel),
        "locator": rel,
        "status": "FOUND" if exists else "MISSING",
        "meta": meta,
    }


def _declared_from_contract(contract: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for i, name in enumerate(contract.get("resources_declared") or []):
        items.append(
            {
                "resource_id": f"declared:{i}:{name}",
                "kind": "other",
                "locator": str(name),
                "status": "DECLARED",
                "meta": {},
            }
        )
    for i, eng in enumerate(contract.get("engines_allowed") or []):
        items.append(
            {
                "resource_id": f"engine:{eng}",
                "kind": "engine",
                "locator": str(eng),
                "status": "DECLARED",
                "meta": {},
            }
        )
    return items


def build_resource_trace(
    contract: dict[str, Any] | None = None,
    *,
    workspace_root: str | None = None,
    extra_paths: list[str] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Build ResourceTrace from filesystem probes + contract declarations."""
    root_s = workspace_root or os.environ.get("WORDFLOW_WORKSPACE") or os.getcwd()
    root = Path(root_s).resolve()
    contract = contract or {}
    contract_id = contract.get("contract_id") or "none"

    paths = list(DEFAULT_PROBE_PATHS)
    if extra_paths:
        paths.extend(extra_paths)
    # de-dupe preserve order
    seen: set[str] = set()
    ordered: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            ordered.append(p)

    items: list[dict[str, Any]] = [_probe_path(root, p) for p in ordered]
    items.extend(_declared_from_contract(contract))

    found = sum(1 for i in items if i["status"] == "FOUND")
    missing = sum(1 for i in items if i["status"] == "MISSING")
    declared = sum(1 for i in items if i["status"] == "DECLARED")
    missing_ids = [i["resource_id"] for i in items if i["status"] == "MISSING"]

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "trace_id": trace_id or f"rt_{uuid.uuid4().hex[:12]}",
        "contract_id": contract_id,
        "scanned_at": _now(),
        "workspace_root": str(root),
        "items": items,
        "summary": {
            "found": found,
            "missing": missing,
            "declared": declared,
            "total": len(items),
        },
        "missing_ids": missing_ids,
    }
    body["trace_hash"] = _hash({k: v for k, v in body.items() if k != "trace_hash"})
    return body


def trace_gate(trace: dict[str, Any], *,
               require_paths: list[str] | None = None) -> dict[str, Any]:
    """PASS if required paths are FOUND. Default: no hard requirements."""
    require_paths = require_paths or []
    by_locator = {i["locator"]: i for i in trace.get("items", []) if i.get("kind") in {"path", "file", "schema", "extension"}}
    missing_required = []
    for rel in require_paths:
        item = by_locator.get(rel)
        if item is None or item["status"] != "FOUND":
            missing_required.append(rel)
    ok = len(missing_required) == 0
    return {
        "ok": ok,
        "missing_required": missing_required,
        "summary": trace.get("summary"),
        "trace_id": trace.get("trace_id"),
        "reason": "TRACE_OK" if ok else "REQUIRED_RESOURCES_MISSING",
    }
