from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "yaiwes.component24.safe-finalizer/v1"


def _jsonable(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return "<depth-limit>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in list(value.items())[:100]}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v, depth + 1) for v in list(value)[:100]]
    return repr(value)[:500]


def _digest(value: Any) -> str:
    raw = json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_workflow(
    *,
    task: dict[str, Any],
    previous_output: Any,
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Finalize and attest the completed benign workflow chain.

    Local safe implementation only. It does not claim to reconstruct
    unavailable upstream code and performs no network, shell, scanning,
    exploitation, or other external side effect.
    """
    if len(history) != 23:
        raise RuntimeError(f"YAIWES 24 requires exactly 23 prior released links, got {len(history)}")

    expected = [f"YAIWES {i:02d}" for i in range(1, 24)]
    actual = [str(item.get("component")) for item in history]
    if actual != expected:
        raise RuntimeError("YAIWES 24 received a non-canonical or non-linear history")
    if not all(item.get("status") == "RELEASED" for item in history):
        raise RuntimeError("YAIWES 24 refuses incomplete upstream state")
    if not all(item.get("real_internal_workflow") is True for item in history):
        raise RuntimeError("YAIWES 24 refuses checkpoint-only upstream state")

    continuity = all(
        history[i]["input_hash"] == history[i - 1]["output_hash"]
        for i in range(1, len(history))
    )
    if not continuity:
        raise RuntimeError("YAIWES 24 refuses broken handoff continuity")

    previous_hash = _digest(previous_output)
    if previous_hash != history[-1]["output_hash"]:
        raise RuntimeError("YAIWES 24 input does not match YAIWES 23 output")

    return {
        "schema": SCHEMA,
        "status": "FINALIZED",
        "implementation_origin": "LOCAL_SAFE_REPLACEMENT",
        "task_digest": _digest(task),
        "input_digest": previous_hash,
        "validated_upstream_components": 23,
        "upstream_continuity": True,
        "effects": "NONE",
        "handoff": "UNIVERSAL_PLUG",
    }
