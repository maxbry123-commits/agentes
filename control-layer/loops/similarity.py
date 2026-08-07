"""Similarity simple para experience graph · 0% LLM
SOURCE: P3 · Jaccard + token overlap (sin vectors externos)
"""
from __future__ import annotations
import re
from typing import Iterable


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def rank_similar(query: str, candidates: Iterable[tuple[str, str]], limit: int = 5) -> list[tuple[str, float]]:
    """candidates: (id, text) → [(id, score)] sorted desc."""
    scored = [(cid, jaccard(query, text)) for cid, text in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


def fingerprint_similarity(fp_a: str, fp_b: str) -> float:
    if fp_a == fp_b:
        return 1.0
    # prefix match soft
    n = min(len(fp_a), len(fp_b), 16)
    if n == 0:
        return 0.0
    same = sum(1 for i in range(n) if fp_a[i] == fp_b[i])
    return same / n
