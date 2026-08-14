# -*- coding: utf-8 -*-
"""CapabilityIntentResolver — T37. Intent → capabilities. 0% LLM."""
from __future__ import annotations

from typing import Any

# keyword → capability tags (deterministic)
_RULES: list[tuple[list[str], list[str]]] = [
    (["code", "implement", "refactor", "patch"], ["code", "tests", "repo"]),
    (["search", "research", "investigate"], ["search", "web", "docs"]),
    (["deploy", "publish", "release"], ["github_publish", "release"]),
    (["skill", "dataset", "adapter", "hf"], ["hf_index", "resource"]),
    (["recover", "retry", "checkpoint"], ["recovery", "checkpoint"]),
    (["plan", "architect", "design"], ["planning", "panel"]),
]


def resolve_intent(
    text: str,
    *,
    task_class: str | None = None,
    extra: list[str] | None = None,
) -> dict[str, Any]:
    t = (text or "").lower()
    caps: list[str] = []
    matched_rules: list[str] = []
    for keywords, need in _RULES:
        if any(k in t for k in keywords):
            for c in need:
                if c not in caps:
                    caps.append(c)
            matched_rules.append(",".join(keywords[:2]))

    if task_class:
        tc = task_class.upper()
        if tc == "CODE" and "code" not in caps:
            caps.extend(["code", "tests"])
        if tc == "SEARCH" and "search" not in caps:
            caps.append("search")

    for c in extra or []:
        if c not in caps:
            caps.append(c)

    if not caps:
        caps = ["general"]

    return {
        "ok": True,
        "intent_text": text,
        "task_class": task_class,
        "capabilities": caps,
        "matched_rules": matched_rules,
        "plan": {
            "capability_resolver": "done",
            "next": ["engine_resolver", "tool_resolver", "sandbox_resolver"],
        },
    }
