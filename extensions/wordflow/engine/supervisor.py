# -*- coding: utf-8 -*-
"""Supervisor — W4. Checkpoint dict + TTL. Deterministic. 0% LLM."""
from __future__ import annotations

import time
from typing import Any


def make_checkpoint(
    *,
    block_hash: str | None,
    step_id: str,
    step_name: str,
    steps_ok: int,
    steps_total: int,
    status: str,
    ttl_seconds: float = 3600.0,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a checkpoint record with absolute expiry."""
    now = time.time()
    cp: dict[str, Any] = {
        "block_hash": block_hash,
        "step_id": step_id,
        "step_name": step_name,
        "steps_ok": steps_ok,
        "steps_total": steps_total,
        "status": status,
        "created_at": now,
        "ttl_seconds": ttl_seconds,
        "expires_at": now + ttl_seconds,
    }
    if extra:
        cp["extra"] = extra
    return cp


def is_expired(checkpoint: dict[str, Any] | None, *, now: float | None = None) -> bool:
    """True if checkpoint missing or past expires_at."""
    if not checkpoint:
        return True
    exp = checkpoint.get("expires_at")
    if exp is None:
        return True
    return (now if now is not None else time.time()) > float(exp)


def validate_checkpoint(checkpoint: dict[str, Any] | None) -> dict[str, Any]:
    """Return {ok, reason, checkpoint}.

    reason: OK | MISSING | EXPIRED
    """
    if not checkpoint:
        return {"ok": False, "reason": "MISSING", "checkpoint": None}
    if is_expired(checkpoint):
        return {"ok": False, "reason": "EXPIRED", "checkpoint": checkpoint}
    return {"ok": True, "reason": "OK", "checkpoint": checkpoint}


def refresh_ttl(
    checkpoint: dict[str, Any],
    *,
    ttl_seconds: float | None = None,
) -> dict[str, Any]:
    """Extend TTL from now; preserves other fields."""
    out = dict(checkpoint)
    ttl = float(ttl_seconds if ttl_seconds is not None else out.get("ttl_seconds", 3600.0))
    now = time.time()
    out["ttl_seconds"] = ttl
    out["expires_at"] = now + ttl
    out["refreshed_at"] = now
    return out
