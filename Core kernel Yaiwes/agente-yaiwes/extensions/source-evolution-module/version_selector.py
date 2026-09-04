# -*- coding: utf-8 -*-
"""Version / quality selector — A-WF-08. never_MVP weights. 0% LLM."""
from __future__ import annotations

from typing import Any

WEIGHTS = {
    "has_tests": 3,
    "has_ci": 3,
    "has_schema": 2,
    "has_docs": 1,
    "loc_ok": 2,
    "pinned_commit": 2,
    "never_mvp_flag": 4,
}

MIN_SCORE_NEVER_MVP = 8
MIN_SCORE_STANDARD = 4


def score_candidate(candidate: dict[str, Any], *, quality_bar: str = "standard") -> dict[str, Any]:
    points = 0
    detail: dict[str, int] = {}

    for key, w in WEIGHTS.items():
        if key == "loc_ok":
            loc = candidate.get("loc")
            ok = loc is None or int(loc) <= 300
            if ok:
                points += w
                detail["loc_ok"] = w
            continue
        if key == "never_mvp_flag":
            if candidate.get("never_mvp") or quality_bar == "never_MVP":
                points += w
                detail["never_mvp_flag"] = w
            continue
        flag = key
        if candidate.get(flag):
            points += w
            detail[flag] = w

    threshold = (
        MIN_SCORE_NEVER_MVP if quality_bar == "never_MVP" else MIN_SCORE_STANDARD
    )
    accepted = points >= threshold
    if quality_bar == "never_MVP" and candidate.get("is_mvp"):
        accepted = False
        detail["mvp_hard_reject"] = -99

    return {
        "score": points,
        "threshold": threshold,
        "accepted": accepted,
        "detail": detail,
        "quality_bar": quality_bar,
    }


def select_best(
    candidates: list[dict[str, Any]],
    *,
    quality_bar: str = "standard",
) -> dict[str, Any]:
    ranked = []
    for i, c in enumerate(candidates):
        s = score_candidate(c, quality_bar=quality_bar)
        ranked.append({"index": i, "candidate": c, **s})
    ranked.sort(key=lambda x: x["score"], reverse=True)

    accepted = [r for r in ranked if r["accepted"]]
    if not accepted:
        return {
            "selected": None,
            "reason": "NO_CANDIDATE_ACCEPTED",
            "ranked": ranked,
            "quality_bar": quality_bar,
        }
    best = accepted[0]
    return {
        "selected": best["candidate"],
        "score": best["score"],
        "index": best["index"],
        "reason": "OK",
        "ranked": ranked,
        "quality_bar": quality_bar,
    }
