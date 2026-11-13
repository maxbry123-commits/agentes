# -*- coding: utf-8 -*-
"""Capability Passport — T11. Issue/verify/authorize. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

SUBJECT_KINDS = frozenset({"engine", "agent", "extension", "worker", "tool", "other"})
STATUSES = frozenset({"ACTIVE", "REVOKED", "EXPIRED"})


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _body(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": p["schema_version"],
        "passport_id": p["passport_id"],
        "subject_id": p["subject_id"],
        "subject_kind": p["subject_kind"],
        "capabilities": sorted(list(p.get("capabilities") or [])),
        "denied": sorted(list(p.get("denied") or [])),
        "lock_id": p.get("lock_id"),
        "status": p["status"],
    }


def issue_passport(
    *,
    subject_id: str,
    subject_kind: str,
    capabilities: list[str],
    denied: list[str] | None = None,
    lock_id: str | None = None,
    status: str = "ACTIVE",
) -> dict[str, Any]:
    if subject_kind not in SUBJECT_KINDS:
        raise ValueError(f"invalid subject_kind={subject_kind}")
    if status not in STATUSES:
        raise ValueError(f"invalid status={status}")
    if not subject_id:
        raise ValueError("subject_id required")

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "passport_id": f"pp_{uuid.uuid4().hex[:12]}",
        "subject_id": subject_id,
        "subject_kind": subject_kind,
        "capabilities": sorted(set(str(c) for c in capabilities)),
        "denied": sorted(set(str(d) for d in (denied or []))),
        "lock_id": lock_id,
        "status": status,
    }
    body["passport_hash"] = _hash(_body(body))
    return body


def verify_passport(passport: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(passport, dict):
        return {"ok": False, "reason": "INVALID_PASSPORT"}
    if passport.get("status") != "ACTIVE":
        return {"ok": False, "reason": f"STATUS_{passport.get('status')}"}
    expected = _hash(_body(passport))
    if passport.get("passport_hash") != expected:
        return {"ok": False, "reason": "PASSPORT_HASH_MISMATCH"}
    return {"ok": True, "reason": "PASSPORT_OK", "passport_id": passport.get("passport_id")}


def authorize(
    passport: dict[str, Any],
    capability: str,
) -> dict[str, Any]:
    """Check single capability string against passport."""
    v = verify_passport(passport)
    if not v["ok"]:
        return {"ok": False, "reason": v["reason"], "capability": capability}

    cap = str(capability)
    denied = set(passport.get("denied") or [])
    allowed = set(passport.get("capabilities") or [])

    if cap in denied:
        return {"ok": False, "reason": "EXPLICITLY_DENIED", "capability": cap}
    if cap in allowed:
        return {"ok": True, "reason": "ALLOWED", "capability": cap}
    # prefix wildcards: resource:* grants resource:read
    for a in allowed:
        if a.endswith(":*") and cap.startswith(a[:-1]):
            return {"ok": True, "reason": "ALLOWED_PREFIX", "capability": cap, "via": a}
    return {"ok": False, "reason": "NOT_IN_CAPABILITIES", "capability": cap}


def default_engine_passport(engine_id: str) -> dict[str, Any]:
    """Minimal safe passport for fake engines."""
    return issue_passport(
        subject_id=engine_id,
        subject_kind="engine",
        capabilities=[
            "route:ANALYSIS",
            "route:DETERMINISTIC",
            "route:PLANNING",
            "resource:read",
            "bus:receive_job",
        ],
        denied=["resource:fetch_remote", "goal:rewrite", "bus:bypass"],
    )
