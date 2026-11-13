# -*- coding: utf-8 -*-
"""C-29 hf_resolver — resolve HF skill/dataset/adapter refs without fetch. 0% LLM."""
from __future__ import annotations

from typing import Any

from .hf_index import HFIndex
from .resource_gate import POST_WORDFLOW_FETCH_ENABLED


class HFResolverError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def resolve_hf_ref(
    ref: str,
    *,
    index: Any = None,
    kind: str | None = None,
) -> dict[str, Any]:
    """Resolve hf://org/name against local index. Never downloads."""
    if not ref:
        raise HFResolverError("REF_EMPTY")

    idx = index
    matches: list[dict[str, Any]] = []
    if idx is not None and hasattr(idx, "search"):
        matches = list(idx.search(ref) or [])
    elif idx is not None and hasattr(idx, "list"):
        for e in idx.list():
            if ref in str(e):
                matches.append(e)

    return {
        "ok": True,
        "ref": ref,
        "kind": kind,
        "matches": matches,
        "fetchable": bool(POST_WORDFLOW_FETCH_ENABLED),
        "action": "FETCH" if POST_WORDFLOW_FETCH_ENABLED else "PLAN_ONLY",
        "reason": None if POST_WORDFLOW_FETCH_ENABLED else "REMOTE_FETCH_DENIED_PRE_POST_WORDFLOW",
        "llm_control": "DENY",
    }


def batch_resolve(refs: list[str], **kwargs: Any) -> dict[str, Any]:
    if not refs:
        raise HFResolverError("NO_REFS")
    results = [resolve_hf_ref(r, **kwargs) for r in refs]
    return {
        "ok": True,
        "count": len(results),
        "results": results,
        "llm_control": "DENY",
    }
