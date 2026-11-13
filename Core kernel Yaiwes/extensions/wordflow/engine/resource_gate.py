# -*- coding: utf-8 -*-
"""ResourceGate — T10. Authorize catalog access / deny remote fetch. 0% LLM."""
from __future__ import annotations

from typing import Any

from .resource_catalog import ResourceCatalog, verify_entry

# Until PIPELINE/32 steps 2–3 complete, remote fetch is denied.
POST_WORDFLOW_FETCH_ENABLED = False

REMOTE_SOURCES = frozenset({"hf", "github", "url"})


def check_entry(entry: dict[str, Any], *,
                action: str = "read") -> dict[str, Any]:
    """action: read | prepare | fetch"""
    v = verify_entry(entry)
    if not v["ok"]:
        return {"ok": False, "reason": v["reason"], "action": action}

    source = entry.get("source")
    if action == "read":
        return {
            "ok": True,
            "reason": "READ_OK",
            "action": action,
            "resource_id": entry.get("resource_id"),
        }

    if action == "prepare":
        # prepare = plan only, no network
        return {
            "ok": True,
            "reason": "PREPARE_OK",
            "action": action,
            "resource_id": entry.get("resource_id"),
            "fetchable": bool(entry.get("fetchable")),
        }

    if action == "fetch":
        if source in REMOTE_SOURCES and not POST_WORDFLOW_FETCH_ENABLED:
            return {
                "ok": False,
                "reason": "REMOTE_FETCH_DENIED_PRE_POST_WORDFLOW",
                "action": action,
                "source": source,
                "resource_id": entry.get("resource_id"),
            }
        if not entry.get("fetchable"):
            return {
                "ok": False,
                "reason": "NOT_FETCHABLE",
                "action": action,
                "resource_id": entry.get("resource_id"),
            }
        if source == "local" and entry.get("fetchable"):
            return {
                "ok": True,
                "reason": "LOCAL_FETCH_OK",
                "action": action,
                "resource_id": entry.get("resource_id"),
            }
        return {
            "ok": False,
            "reason": "FETCH_DENIED",
            "action": action,
            "resource_id": entry.get("resource_id"),
        }

    return {"ok": False, "reason": f"UNKNOWN_ACTION_{action}", "action": action}


def gate_catalog_get(
    catalog: ResourceCatalog,
    resource_id: str,
    *,
    action: str = "read",
) -> dict[str, Any]:
    entry = catalog.get(resource_id)
    if entry is None:
        return {"ok": False, "reason": "NOT_FOUND", "resource_id": resource_id}
    result = check_entry(entry, action=action)
    result["entry"] = entry if result["ok"] or action == "read" else None
    if action == "read" and result["ok"]:
        result["entry"] = entry
    elif not result["ok"]:
        result["entry"] = entry  # still return for audit
    return result
