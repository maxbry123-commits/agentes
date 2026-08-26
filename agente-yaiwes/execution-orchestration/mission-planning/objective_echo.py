# -*- coding: utf-8 -*-
"""ObjectiveEcho — T0i. Inject GoalLock into engine context. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .goal_lock import GoalLockError, verify_lock_integrity


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_echo(lock: dict[str, Any]) -> dict[str, Any]:
    """Build immutable echo block from LOCKED GoalLock."""
    integ = verify_lock_integrity(lock)
    if not integ["ok"]:
        raise GoalLockError("LOCK_NOT_INTACT", str(integ.get("reason")))

    objective = lock.get("objective") or ""
    success = lock.get("success_criteria") or ""
    constraints = list(lock.get("constraints") or [])
    forbidden = list(lock.get("forbidden") or [])

    lines = [
        "=== GOAL_LOCK (IMMUTABLE) ===",
        f"lock_id: {lock.get('lock_id')}",
        f"objective: {objective}",
        f"success_criteria: {success}",
    ]
    if constraints:
        lines.append("constraints:")
        lines.extend(f"  - {c}" for c in constraints)
    if forbidden:
        lines.append("forbidden:")
        lines.extend(f"  - {f}" for f in forbidden)
    lines.append("RULE: Violate objective/forbidden → output DISCARDED.")
    lines.append("=== END GOAL_LOCK ===")
    block = "\n".join(lines)

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "echo_id": f"oe_{uuid.uuid4().hex[:12]}",
        "lock_id": lock.get("lock_id") or "",
        "block": block,
        "fields": {
            "objective": objective,
            "success_criteria": success,
            "constraints": constraints,
            "forbidden": forbidden,
        },
    }
    body["echo_hash"] = _hash({k: v for k, v in body.items() if k != "echo_hash"})
    return body


def inject_echo(lock: dict[str, Any], user_prompt: str) -> dict[str, Any]:
    """Prepend echo block to user prompt. Returns prompt package."""
    echo = build_echo(lock)
    combined = f"{echo['block']}\n\n{user_prompt or ''}".strip()
    return {
        "echo": echo,
        "prompt": combined,
        "lock_id": echo["lock_id"],
        "echo_hash": echo["echo_hash"],
    }
