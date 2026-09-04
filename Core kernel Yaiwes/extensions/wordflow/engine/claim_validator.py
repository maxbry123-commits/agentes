# -*- coding: utf-8 -*-
"""C-22 claim_validator — enforce COMPLETED evidence rules. 0% LLM."""
from __future__ import annotations

from typing import Any

COMPLETED_REQUIRED = ("task_id", "paths", "tests", "doc_anchors")


class ClaimError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def validate_claim(
    claim: dict[str, Any] | None,
    evidence: Any = None,
) -> dict[str, Any]:
    if not isinstance(claim, dict):
        return {
            "ok": False,
            "verdict": "fail",
            "reason_codes": ["CLAIM_NOT_OBJECT"],
            "llm_control": "DENY",
        }

    reasons: list[str] = []
    status = claim.get("claim_status") or claim.get("status")

    ev = evidence if evidence is not None else claim.get("evidence")
    if ev is None or ev == "" or ev == [] or ev == {}:
        if evidence is not None or status == "COMPLETED":
            reasons.append("EVIDENCE_REQUIRED")

    if status not in ("PARTIAL", "COMPLETED", "REFUTADO"):
        if status is not None:
            reasons.append("BAD_STATUS")

    if not claim.get("task_id"):
        reasons.append("TASK_ID_MISSING")

    if status == "COMPLETED":
        paths = claim.get("paths") or []
        if not isinstance(paths, list) or not paths:
            reasons.append("PATHS_REQUIRED")
        else:
            for i, p in enumerate(paths):
                if not isinstance(p, dict):
                    reasons.append(f"PATH_{i}_NOT_OBJECT")
                    continue
                if not p.get("path"):
                    reasons.append(f"PATH_{i}_NO_PATH")
                if not p.get("blob_sha"):
                    reasons.append(f"PATH_{i}_NO_BLOB_SHA")
        tests = claim.get("tests")
        if not isinstance(tests, dict) or not tests:
            reasons.append("TESTS_REQUIRED")
        anchors = claim.get("doc_anchors") or claim.get("doc_anchor")
        if not anchors:
            reasons.append("DOC_ANCHOR_REQUIRED")

    ok = len(reasons) == 0
    return {
        "ok": ok,
        "verdict": "pass" if ok else "fail",
        "reason_codes": reasons,
        "claim_status": status,
        "llm_control": "DENY",
    }


def require_claim(claim: dict[str, Any] | None) -> dict[str, Any]:
    r = validate_claim(claim)
    if not r["ok"]:
        raise ClaimError("CLAIM_INVALID", ",".join(r["reason_codes"]))
    return r


if __name__ == "__main__":
    fail = validate_claim({"task_id": "T30", "status": "COMPLETED"}, evidence=None)
    assert fail["ok"] is False and fail["verdict"] == "fail"
    fail2 = validate_claim({"task_id": "T30"}, evidence={})
    assert fail2["ok"] is False
    print("ok", fail["reason_codes"], fail2["verdict"])
