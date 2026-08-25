# -*- coding: utf-8 -*-
"""Process 03 — Input quality bar (admit/reject)."""
from __future__ import annotations
from typing import Any
from .quality_bar import admit_or_reject, MIN_CHARS_DEFAULT


def run_quality_bar(raw_input: str, wire_trace: dict[str, Any]) -> dict[str, Any] | None:
    q = admit_or_reject(raw_input)
    wire_trace["quality_bar"] = {"ok": q.get("ok"), "reason_codes": q.get("reason_codes"), "min_chars": q.get("min_chars", MIN_CHARS_DEFAULT), "thresholds": q.get("thresholds"), "chars": q.get("chars")}
    if not q.get("ok"):
        return {"ok": False, "stage": "quality_bar", "detail": q, "llm_control": "DENY", "verdict": "FAIL", "wire_trace": wire_trace}
    return None
