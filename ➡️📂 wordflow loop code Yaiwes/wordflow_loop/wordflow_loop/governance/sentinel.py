from __future__ import annotations

import time

from ..contracts import LayerResult, NodeContract


def check_runtime(node: NodeContract, result: LayerResult, started_at: float) -> list[str]:
    errors: list[str] = []
    elapsed_ms = (time.monotonic() - started_at) * 1000
    if elapsed_ms > node.timeout_ms:
        errors.append("timeout_exceeded")
    forbidden = set(result.actions) & set(node.forbidden_actions)
    if forbidden:
        errors.append("forbidden_action:" + ",".join(sorted(forbidden)))
    if node.allowed_actions:
        outside = set(result.actions) - set(node.allowed_actions)
        if outside:
            errors.append("action_outside_allowlist:" + ",".join(sorted(outside)))
    return errors
