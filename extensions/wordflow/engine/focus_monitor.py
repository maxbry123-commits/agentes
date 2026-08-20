# -*- coding: utf-8 -*-
"""FocusMonitor — T0g. Score goal vs step vs output. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .goal_lock import verify_lock_integrity
from .push_ping import compute_focus_score

DEFAULT_THRESHOLD = 0.5


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _band(score: float) -> str:
    if score <= 0.0:
        return "ZERO"
    if score < 0.5:
        return "LOW"
    if score < 0.75:
        return "MED"
    return "HIGH"


def _signals(
    lock: dict[str, Any],
    *,
    current_step: str | None,
    last_output: str | None,
) -> dict[str, Any]:
    integ = verify_lock_integrity(lock)
    obj = (lock.get("objective") or "").lower()
    tokens = [w for w in obj.replace(",", " ").split() if len(w) > 3]
    hay = f"{current_step or ''} {last_output or ''}".lower()
    empty = not hay.strip()
    hits = 0 if empty else sum(1 for t in tokens[:8] if t in hay)
    forbidden_hit = False
    for term in lock.get("forbidden") or []:
        t = str(term).strip().lower()
        if t and t in hay and f"sin {t}" not in hay and f"without {t}" not in hay:
            forbidden_hit = True
            break
    return {
        "lock_ok": bool(integ["ok"]),
        "token_hits": hits,
        "token_total": min(8, len(tokens)),
        "forbidden_hit": forbidden_hit,
        "empty_context": empty,
    }


def evaluate_focus(
    lock: dict[str, Any],
    *,
    current_step: str | None = None,
    last_output: str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """Full FocusReport for supervisors and gates."""
    score = compute_focus_score(
        lock, current_step=current_step, last_output=last_output
    )
    sig = _signals(lock, current_step=current_step, last_output=last_output)
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "report_id": f"fr_{uuid.uuid4().hex[:12]}",
        "lock_id": lock.get("lock_id") or "",
        "score": score,
        "band": _band(score),
        "threshold": threshold,
        "below_threshold": score < threshold,
        "signals": sig,
        "current_step": current_step,
    }
    body["report_hash"] = _hash({k: v for k, v in body.items() if k != "report_hash"})
    return body


def focus_gate(
    lock: dict[str, Any],
    *,
    current_step: str | None = None,
    last_output: str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """PASS if score >= threshold and lock ok."""
    report = evaluate_focus(
        lock,
        current_step=current_step,
        last_output=last_output,
        threshold=threshold,
    )
    ok = (
        report["signals"]["lock_ok"]
        and not report["below_threshold"]
        and not report["signals"]["forbidden_hit"]
    )
    return {
        "ok": ok,
        "reason": "FOCUS_OK" if ok else "FOCUS_FAIL",
        "report": report,
    }
