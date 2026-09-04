# -*- coding: utf-8 -*-
"""Execution Manifest — T5. Sign + verify. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(text: str | None) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _body_for_hash(m: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": m["schema_version"],
        "manifest_id": m["manifest_id"],
        "lock_id": m["lock_id"],
        "engine_id": m["engine_id"],
        "route": m["route"],
        "job_fingerprint": m.get("job_fingerprint") or {},
        "constraints_snapshot": list(m.get("constraints_snapshot") or []),
        "forbidden_snapshot": list(m.get("forbidden_snapshot") or []),
        "created_at": m["created_at"],
    }


def sign_manifest(
    *,
    lock: dict[str, Any],
    job: dict[str, Any],
    manifest_id: str | None = None,
) -> dict[str, Any]:
    """Create signed manifest from lock + job input fingerprints."""
    inp = job.get("input") or {}
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "manifest_id": manifest_id or f"man_{uuid.uuid4().hex[:12]}",
        "lock_id": lock.get("lock_id") or job.get("lock_id") or "",
        "engine_id": job.get("engine_id") or "",
        "route": job.get("route") or "",
        "job_fingerprint": {
            "prompt_sha256": _sha(inp.get("prompt") or ""),
            "echo_sha256": _sha(inp.get("echo_block")),
            "registers_sha256": _sha(inp.get("registers_block")),
        },
        "constraints_snapshot": list(lock.get("constraints") or []),
        "forbidden_snapshot": list(lock.get("forbidden") or []),
        "created_at": _now(),
    }
    body["manifest_hash"] = _hash(_body_for_hash(body))
    return body


def verify_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        return {"ok": False, "reason": "INVALID_MANIFEST"}
    expected = _hash(_body_for_hash(manifest))
    actual = manifest.get("manifest_hash")
    if actual != expected:
        return {"ok": False, "reason": "HASH_MISMATCH", "expected": expected, "actual": actual}
    return {"ok": True, "reason": "MANIFEST_OK", "manifest_id": manifest.get("manifest_id")}


def attach_manifest_to_job(job: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Return new job with manifest_id set. Does not mutate original."""
    out = dict(job)
    out["manifest_id"] = manifest["manifest_id"]
    # recompute job_hash without changing other fields
    from .engine_abi import make_job  # avoid circular at top for hash rebuild pattern

    rebuilt = make_job(
        lock_id=out.get("lock_id") or "",
        engine_id=out.get("engine_id") or "",
        route=out.get("route") or "ANALYSIS",
        prompt=(out.get("input") or {}).get("prompt") or "",
        echo_block=(out.get("input") or {}).get("echo_block"),
        registers_block=(out.get("input") or {}).get("registers_block"),
        extra=(out.get("input") or {}).get("extra"),
        manifest_id=manifest["manifest_id"],
        timeout_s=float(out.get("timeout_s") or 60),
    )
    # keep original job_id if present
    if job.get("job_id"):
        rebuilt["job_id"] = job["job_id"]
        body = {k: v for k, v in rebuilt.items() if k != "job_hash"}
        rebuilt["job_hash"] = _hash(body)
    return rebuilt


def job_matches_manifest(job: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Ensure job input fingerprints match signed manifest."""
    v = verify_manifest(manifest)
    if not v["ok"]:
        return v
    if job.get("manifest_id") != manifest.get("manifest_id"):
        return {"ok": False, "reason": "MANIFEST_ID_MISMATCH"}
    if job.get("lock_id") and job["lock_id"] != manifest.get("lock_id"):
        return {"ok": False, "reason": "LOCK_ID_MISMATCH"}
    if job.get("engine_id") != manifest.get("engine_id"):
        return {"ok": False, "reason": "ENGINE_ID_MISMATCH"}
    inp = job.get("input") or {}
    fp = manifest.get("job_fingerprint") or {}
    if _sha(inp.get("prompt") or "") != fp.get("prompt_sha256"):
        return {"ok": False, "reason": "PROMPT_FINGERPRINT_MISMATCH"}
    if _sha(inp.get("echo_block")) != fp.get("echo_sha256"):
        return {"ok": False, "reason": "ECHO_FINGERPRINT_MISMATCH"}
    if _sha(inp.get("registers_block")) != fp.get("registers_sha256"):
        return {"ok": False, "reason": "REGISTERS_FINGERPRINT_MISMATCH"}
    return {"ok": True, "reason": "JOB_MATCHES_MANIFEST"}
