# -*- coding: utf-8 -*-
"""ArtifactPin — T8. Immutable artifact identity. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

ALLOWED_KINDS = frozenset({"file", "uri", "blob", "hf_repo", "git_ref", "other"})


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _body_for_hash(pin: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": pin["schema_version"],
        "pin_id": pin["pin_id"],
        "kind": pin["kind"],
        "ref": pin["ref"],
        "content_sha256": pin["content_sha256"],
        "size_bytes": pin.get("size_bytes"),
        "media_type": pin.get("media_type"),
        "lock_id": pin.get("lock_id"),
        "labels": list(pin.get("labels") or []),
    }


def content_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_sha256_text(text: str) -> str:
    return content_sha256_bytes(text.encode("utf-8"))


def pin_from_bytes(
    data: bytes,
    *,
    kind: str = "blob",
    ref: str,
    lock_id: str | None = None,
    media_type: str | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"invalid kind={kind}")
    if not ref:
        raise ValueError("ref required")
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "pin_id": f"pin_{uuid.uuid4().hex[:12]}",
        "kind": kind,
        "ref": ref,
        "content_sha256": content_sha256_bytes(data),
        "size_bytes": len(data),
        "media_type": media_type,
        "lock_id": lock_id,
        "labels": list(labels or []),
    }
    body["pin_hash"] = _hash(_body_for_hash(body))
    return body


def pin_from_text(
    text: str,
    *,
    kind: str = "blob",
    ref: str,
    lock_id: str | None = None,
    media_type: str | None = "text/plain",
    labels: list[str] | None = None,
) -> dict[str, Any]:
    return pin_from_bytes(
        text.encode("utf-8"),
        kind=kind,
        ref=ref,
        lock_id=lock_id,
        media_type=media_type,
        labels=labels,
    )


def pin_from_path(
    path: str | Path,
    *,
    lock_id: str | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    p = Path(path)
    data = p.read_bytes()
    return pin_from_bytes(
        data,
        kind="file",
        ref=str(p),
        lock_id=lock_id,
        media_type=None,
        labels=labels,
    )


def verify_pin(pin: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(pin, dict):
        return {"ok": False, "reason": "INVALID_PIN"}
    if pin.get("kind") not in ALLOWED_KINDS:
        return {"ok": False, "reason": "INVALID_KIND"}
    if not pin.get("ref") or not pin.get("content_sha256"):
        return {"ok": False, "reason": "MISSING_FIELDS"}
    expected = _hash(_body_for_hash(pin))
    if pin.get("pin_hash") != expected:
        return {"ok": False, "reason": "PIN_HASH_MISMATCH", "expected": expected}
    return {"ok": True, "reason": "PIN_OK", "pin_id": pin.get("pin_id")}


def verify_content(pin: dict[str, Any], data: bytes) -> dict[str, Any]:
    v = verify_pin(pin)
    if not v["ok"]:
        return v
    actual = content_sha256_bytes(data)
    if actual != pin.get("content_sha256"):
        return {"ok": False, "reason": "CONTENT_MISMATCH", "actual": actual}
    return {"ok": True, "reason": "CONTENT_OK", "pin_id": pin.get("pin_id")}
