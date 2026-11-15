"""T25 — 12-stage hooks isolated by instance_id. No LLM."""
from __future__ import annotations

from typing import Any, Callable

Hook = Callable[[str, int], dict[str, Any]]

STAGES = tuple(range(1, 13))
_HOOKS: dict[str, dict[int, Hook]] = {}
_LAST: dict[str, dict[int, dict[str, Any]]] = {}


def _default_hook(instance_id: str, n: int) -> dict[str, Any]:
    return {
        "ok": True,
        "instance_id": instance_id,
        "stage": n,
        "llm": False,
        "mode": "stub",
    }


def register_hooks(instance_id: str, hooks: dict[int, Hook] | None = None) -> dict[int, Hook]:
    table = {n: _default_hook for n in STAGES}
    if hooks:
        for n, fn in hooks.items():
            if n in table:
                table[int(n)] = fn
    _HOOKS[instance_id] = table
    _LAST.setdefault(instance_id, {})
    return table


def run_stage(instance_id: str, n: int) -> dict[str, Any]:
    n = int(n)
    if n not in STAGES:
        return {"ok": False, "instance_id": instance_id, "stage": n, "error": "invalid_stage"}
    table = _HOOKS.get(instance_id) or register_hooks(instance_id)
    out = table[n](instance_id, n)
    _LAST.setdefault(instance_id, {})[n] = out
    return out


def last_stage(instance_id: str, n: int) -> dict[str, Any] | None:
    return _LAST.get(instance_id, {}).get(n)


if __name__ == "__main__":
    def mark_a(iid, n):
        return {"ok": True, "instance_id": iid, "stage": n, "mark": "A"}

    def mark_b(iid, n):
        return {"ok": True, "instance_id": iid, "stage": n, "mark": "B"}

    register_hooks("v1", {1: mark_a})
    register_hooks("v2", {1: mark_b})
    a = run_stage("v1", 1)
    b = run_stage("v2", 1)
    assert a["mark"] != b["mark"]
    assert run_stage("v1", 12)["ok"] is True
    print("ok", a["mark"], b["mark"], run_stage("v1", 2)["llm"])
