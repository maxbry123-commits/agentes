# -*- coding: utf-8 -*-
"""Watchdog — W3. Deterministic stop triggers. 0% LLM."""
from __future__ import annotations

import re
import time
from typing import Any

# Patterns that must never appear in loop state / logs
_SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
)


def check_watchdog(
    *,
    step_id: str,
    step_name: str,
    started_at: float,
    timeout_seconds: float = 120.0,
    last_step_id: str | None = None,
    same_step_count: int = 0,
    stuck_threshold: int = 3,
    text_blobs: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluate stop triggers.

    Returns:
        {"ok": True} or {"ok": False, "action": "stop", "reason": CODE, "detail": ...}
    """
    # 1) timeout
    elapsed = time.monotonic() - started_at
    if elapsed > timeout_seconds:
        return {
            "ok": False,
            "action": "stop",
            "reason": "TIMEOUT",
            "detail": {"elapsed": round(elapsed, 3), "limit": timeout_seconds},
        }

    # 2) stuck on same step
    if last_step_id == step_id and same_step_count >= stuck_threshold:
        return {
            "ok": False,
            "action": "stop",
            "reason": "STUCK_STEP",
            "detail": {
                "step_id": step_id,
                "step_name": step_name,
                "count": same_step_count,
                "threshold": stuck_threshold,
            },
        }

    # 3) secret leak in text blobs
    for blob in text_blobs or []:
        if not isinstance(blob, str):
            continue
        for pat in _SECRET_PATTERNS:
            if pat.search(blob):
                return {
                    "ok": False,
                    "action": "stop",
                    "reason": "SECRET_LEAK",
                    "detail": {"step_id": step_id, "pattern": pat.pattern[:40]},
                }

    return {"ok": True, "action": "continue", "reason": None, "detail": None}


def scan_state_for_secrets(state: dict[str, Any]) -> list[str]:
    """Collect string leaves from state for secret scan (shallow+one level)."""
    blobs: list[str] = []
    for v in state.values():
        if isinstance(v, str):
            blobs.append(v)
        elif isinstance(v, dict):
            for vv in v.values():
                if isinstance(vv, str):
                    blobs.append(vv)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    blobs.append(item)
                elif isinstance(item, dict):
                    for vv in item.values():
                        if isinstance(vv, str):
                            blobs.append(vv)
    return blobs
