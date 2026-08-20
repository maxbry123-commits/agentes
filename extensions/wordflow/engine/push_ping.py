# -*- coding: utf-8 -*-
"""Push/Ping supervisor — T0f. Interval 15s + post-tool. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from .goal_lock import verify_lock_integrity

DEFAULT_INTERVAL_S = 15
DEFAULT_FOCUS_THRESHOLD = 0.5


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_focus_score(
    lock: dict[str, Any],
    *,
    current_step: str | None = None,
    last_output: str | None = None,
) -> float:
    """Deterministic focus score 0..1 from lock vs step/output tokens."""
    integ = verify_lock_integrity(lock)
    if not integ["ok"]:
        return 0.0

    obj = (lock.get("objective") or "").lower()
    tokens = [w for w in obj.replace(",", " ").split() if len(w) > 3]
    if not tokens:
        return 1.0 if integ["ok"] else 0.0

    hay = f"{current_step or ''} {last_output or ''}".lower()
    if not hay.strip():
        # no context yet — assume focused if lock intact
        return 0.85

    hits = sum(1 for t in tokens[:8] if t in hay)
    ratio = hits / min(8, len(tokens))
    # forbidden presence collapses score
    for term in lock.get("forbidden") or []:
        t = str(term).strip().lower()
        if t and t in hay and f"sin {t}" not in hay and f"without {t}" not in hay:
            return min(ratio * 0.3, 0.2)
    return round(min(1.0, 0.4 + ratio * 0.6), 3)


def emit_ping(
    lock: dict[str, Any],
    *,
    trigger: str = "interval",
    current_step: str | None = None,
    last_output: str | None = None,
    lease_alive: bool = True,
    checkpoint_ref: str | None = None,
    focus_threshold: float = DEFAULT_FOCUS_THRESHOLD,
) -> dict[str, Any]:
    """One ping event. No LLM. No Hermes call (deferred PIPELINE/32)."""
    if trigger not in ("interval", "post_tool", "manual"):
        raise ValueError(f"invalid trigger={trigger}")

    integ = verify_lock_integrity(lock)
    focus = compute_focus_score(
        lock, current_step=current_step, last_output=last_output
    )
    reasons: list[str] = []

    if not integ["ok"]:
        action = "ABORT_CORRUPT_LOCK"
        reasons.append(str(integ.get("reason") or "integrity_fail"))
    elif not lease_alive:
        action = "STOP_REPLAN"
        reasons.append("lease_dead")
    elif focus < focus_threshold:
        action = "STOP_REPLAN"
        reasons.append(f"focus_below_{focus_threshold}")
    else:
        action = "CONTINUE"

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "ping_id": f"ping_{uuid.uuid4().hex[:12]}",
        "lock_id": lock.get("lock_id") or "",
        "trigger": trigger,
        "ts": _now(),
        "lock_integrity_ok": bool(integ["ok"]),
        "focus_score": focus,
        "lease_alive": bool(lease_alive),
        "checkpoint_ref": checkpoint_ref,
        "action": action,
        "reasons": reasons,
    }
    body["ping_hash"] = _hash({k: v for k, v in body.items() if k != "ping_hash"})
    return body


class PushPingSupervisor:
    """Tracks last ping time; interval + post_tool triggers."""

    def __init__(
        self,
        lock: dict[str, Any],
        *,
        interval_s: float = DEFAULT_INTERVAL_S,
        focus_threshold: float = DEFAULT_FOCUS_THRESHOLD,
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ):
        self.lock = lock
        self.interval_s = interval_s
        self.focus_threshold = focus_threshold
        self.on_event = on_event
        self._last_ping_monotonic: float | None = None
        self.history: list[dict[str, Any]] = []

    def _record(self, event: dict[str, Any], *, now_mono: float | None = None) -> dict[str, Any]:
        self.history.append(event)
        self._last_ping_monotonic = now_mono if now_mono is not None else time.monotonic()
        if self.on_event:
            self.on_event(event)
        return event

    def maybe_interval_ping(
        self,
        *,
        current_step: str | None = None,
        last_output: str | None = None,
        lease_alive: bool = True,
        checkpoint_ref: str | None = None,
        now_mono: float | None = None,
    ) -> dict[str, Any] | None:
        now = now_mono if now_mono is not None else time.monotonic()
        if self._last_ping_monotonic is not None and (now - self._last_ping_monotonic) < self.interval_s:
            return None
        ev = emit_ping(
            self.lock,
            trigger="interval",
            current_step=current_step,
            last_output=last_output,
            lease_alive=lease_alive,
            checkpoint_ref=checkpoint_ref,
            focus_threshold=self.focus_threshold,
        )
        return self._record(ev, now_mono=now)

    def post_tool_ping(
        self,
        *,
        current_step: str | None = None,
        last_output: str | None = None,
        lease_alive: bool = True,
        checkpoint_ref: str | None = None,
    ) -> dict[str, Any]:
        ev = emit_ping(
            self.lock,
            trigger="post_tool",
            current_step=current_step,
            last_output=last_output,
            lease_alive=lease_alive,
            checkpoint_ref=checkpoint_ref,
            focus_threshold=self.focus_threshold,
        )
        return self._record(ev)
