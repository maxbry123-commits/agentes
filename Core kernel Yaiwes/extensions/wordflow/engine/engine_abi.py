# -*- coding: utf-8 -*-
"""Engine ABI — T1. Job/Result builders + Engine Protocol. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Protocol, runtime_checkable

from .goal_lock import validate_against_lock


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_job(
    *,
    lock_id: str,
    engine_id: str,
    route: str,
    prompt: str,
    echo_block: str | None = None,
    registers_block: str | None = None,
    extra: dict[str, Any] | None = None,
    manifest_id: str | None = None,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "job_id": f"job_{uuid.uuid4().hex[:12]}",
        "lock_id": lock_id or "",
        "engine_id": engine_id,
        "route": route,
        "input": {
            "prompt": prompt or "",
            "echo_block": echo_block,
            "registers_block": registers_block,
            "extra": dict(extra or {}),
        },
        "manifest_id": manifest_id,
        "timeout_s": float(timeout_s),
    }
    body["job_hash"] = _hash({k: v for k, v in body.items() if k != "job_hash"})
    return body


def make_result(
    job: dict[str, Any],
    *,
    status: str,
    output_text: str | None = None,
    artifacts: list[str] | None = None,
    error_code: str | None = None,
    error_detail: str | None = None,
    goal_check: dict[str, Any] | None = None,
) -> dict[str, Any]:
    allowed = {"OK", "ERROR", "TIMEOUT", "DENIED", "DISCARDED"}
    if status not in allowed:
        raise ValueError(f"invalid status={status}")
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "result_id": f"res_{uuid.uuid4().hex[:12]}",
        "job_id": job.get("job_id") or "",
        "engine_id": job.get("engine_id") or "",
        "status": status,
        "output_text": output_text,
        "artifacts": list(artifacts or []),
        "error_code": error_code,
        "error_detail": error_detail,
        "goal_check": goal_check,
    }
    body["result_hash"] = _hash({k: v for k, v in body.items() if k != "result_hash"})
    return body


def apply_goal_filter(
    lock: dict[str, Any],
    job: dict[str, Any],
    output_text: str | None,
) -> dict[str, Any]:
    """Post-engine: OK → DISCARDED if GoalLock violated."""
    check = validate_against_lock(lock, output_text or "")
    if check.get("ok"):
        return make_result(job, status="OK", output_text=output_text, goal_check=check)
    return make_result(
        job,
        status="DISCARDED",
        output_text=output_text,
        error_code="GOAL_VIOLATION",
        error_detail=str(check.get("violations") or check.get("reason")),
        goal_check=check,
    )


@runtime_checkable
class Engine(Protocol):
    engine_id: str

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        """Execute job; return EngineResult (pre goal filter optional)."""
        ...
