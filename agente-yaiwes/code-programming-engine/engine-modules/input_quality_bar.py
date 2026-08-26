# -*- coding: utf-8 -*-
"""C-13/U6 input_quality_bar — thresholds explícitos en result."""
from __future__ import annotations

import re
from typing import Any

MVP_MARKERS = re.compile(
    r"\b(mvp\s*only|solo\s*mvp|temporary\s*hack|todo\s*later|fix\s*later)\b",
    re.I,
)
MIN_CHARS_DEFAULT = 40


class QualityBarError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def evaluate_input_quality(
    text: str,
    *,
    min_chars: int = MIN_CHARS_DEFAULT,
    require_objective: bool = True,
    fail_closed: bool = True,
) -> dict[str, Any]:
    reasons: list[str] = []
    raw = text if isinstance(text, str) else ""
    stripped = raw.strip()

    if not stripped:
        reasons.append("EMPTY_INPUT")
    elif len(stripped) < min_chars:
        reasons.append("TOO_SHORT")

    if MVP_MARKERS.search(stripped):
        reasons.append("MVP_MARKER")

    if require_objective:
        has_obj = bool(re.search(r"\b(objetivo|objective|goal|meta)\b", stripped, re.I))
        has_verb = bool(re.search(
            r"\b(implement|build|crear|construir|fix|repair|deploy|auditar|analyze)\b",
            stripped,
            re.I,
        ))
        if not (has_obj or has_verb):
            reasons.append("NO_OBJECTIVE_SIGNAL")

    ok = len(reasons) == 0
    result = {
        "ok": ok,
        "reason_codes": reasons,
        "chars": len(stripped),
        "min_chars": min_chars,
        "require_objective": require_objective,
        "thresholds": {"min_chars": min_chars, "mvp_markers": True, "objective_or_verb": require_objective},
        "llm_control": "DENY",
        "policy": "never_mvp",
    }
    if not ok and fail_closed:
        raise QualityBarError("QUALITY_BAR_REJECT", ",".join(reasons))
    return result


def admit_or_reject(text: str, **kwargs: Any) -> dict[str, Any]:
    try:
        return evaluate_input_quality(text, fail_closed=True, **kwargs)
    except QualityBarError as e:
        return {
            "ok": False,
            "reason_codes": e.detail.split(",") if e.detail else [e.reason_code],
            "min_chars": kwargs.get("min_chars", MIN_CHARS_DEFAULT),
            "thresholds": {"min_chars": kwargs.get("min_chars", MIN_CHARS_DEFAULT)},
            "llm_control": "DENY",
            "policy": "never_mvp",
        }
