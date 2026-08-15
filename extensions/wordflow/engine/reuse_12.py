# -*- coding: utf-8 -*-
"""C-15 reuse_12 — prefer existing catalog artifacts over greenfield. 0% LLM."""
from __future__ import annotations

from typing import Any

from .resource_catalog import ResourceCatalog


class ReuseError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _score(entry: dict[str, Any], query: str, kind: str | None) -> int:
    score = 0
    name = (entry.get("name") or "").lower()
    q = (query or "").lower()
    if not q:
        return 0
    if q == name:
        score += 10
    elif q in name:
        score += 5
    tags = [t.lower() for t in (entry.get("tags") or [])]
    if q in tags:
        score += 3
    if kind and entry.get("kind") == kind:
        score += 2
    return score


def find_reusable(
    catalog: ResourceCatalog,
    *,
    query: str,
    kind: str | None = None,
    min_score: int = 5,
) -> dict[str, Any]:
    if not query:
        raise ReuseError("QUERY_EMPTY")
    ranked = []
    for e in catalog.list(kind=kind):
        s = _score(e, query, kind)
        if s >= min_score:
            ranked.append({"score": s, "entry": e})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {
        "ok": True,
        "query": query,
        "matches": ranked,
        "reuse_recommended": len(ranked) > 0,
        "top": ranked[0]["entry"] if ranked else None,
        "llm_control": "DENY",
    }


def reuse_or_generate(
    catalog: ResourceCatalog,
    *,
    query: str,
    kind: str | None = None,
) -> dict[str, Any]:
    found = find_reusable(catalog, query=query, kind=kind)
    if found["reuse_recommended"]:
        return {
            "ok": True,
            "action": "REUSE",
            "resource_id": found["top"].get("resource_id"),
            "entry": found["top"],
            "llm_control": "DENY",
        }
    return {
        "ok": True,
        "action": "GENERATE",
        "query": query,
        "kind": kind,
        "llm_control": "DENY",
    }


def reuse_12(catalog: ResourceCatalog, query: str, **kwargs: Any) -> dict[str, Any]:
    return reuse_or_generate(catalog, query=query, **kwargs)
