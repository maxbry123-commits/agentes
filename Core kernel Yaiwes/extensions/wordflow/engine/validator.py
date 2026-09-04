# -*- coding: utf-8 -*-
"""Output validator C-03 — fail_closed for architecture_output + code_output. 0% LLM."""
from __future__ import annotations

from typing import Any

ARCH_REQUIRED = ("schema_version", "artifact_id", "files", "evidence_ref")
CODE_REQUIRED = ("schema_version", "artifact_id", "files", "evidence_ref")
EVIDENCE_REQUIRED = ("task_id", "claim_status")
CLAIM_OK = {"PARTIAL", "COMPLETED", "REFUTADO"}
FILE_KINDS = {"yaml", "json", "md", "py", "other"}
FILE_ACTIONS = {"create", "update", "delete"}
LANGUAGES = {"python", "yaml", "json", "markdown", "mixed"}


class ValidatorError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _require(data: dict[str, Any], fields: tuple[str, ...], prefix: str) -> list[str]:
    return [f"{prefix}_MISSING_{f}" for f in fields if f not in data]


def _check_evidence(ev: Any) -> list[str]:
    reasons: list[str] = []
    if not isinstance(ev, dict):
        return ["EVIDENCE_NOT_OBJECT"]
    reasons.extend(_require(ev, EVIDENCE_REQUIRED, "EVIDENCE"))
    status = ev.get("claim_status")
    if status is not None and status not in CLAIM_OK:
        reasons.append(f"EVIDENCE_BAD_CLAIM:{status}")
    return reasons


def validate_architecture_output(data: Any, *, fail_closed: bool = True) -> dict[str, Any]:
    reasons: list[str] = []
    if not isinstance(data, dict):
        reasons.append("NOT_OBJECT")
        if fail_closed:
            raise ValidatorError("ARCH_REJECTED", ",".join(reasons))
        return {"ok": False, "reason_codes": reasons, "kind": "architecture_output"}

    reasons.extend(_require(data, ARCH_REQUIRED, "ARCH"))
    if data.get("schema_version") not in (None, "1.0"):
        reasons.append(f"ARCH_BAD_VERSION:{data.get('schema_version')}")

    files = data.get("files")
    if not isinstance(files, list) or len(files) < 1:
        reasons.append("ARCH_FILES_EMPTY")
    else:
        for i, item in enumerate(files):
            if not isinstance(item, dict):
                reasons.append(f"ARCH_FILE_{i}_NOT_OBJECT")
                continue
            if "path" not in item or not item["path"]:
                reasons.append(f"ARCH_FILE_{i}_NO_PATH")
            kind = item.get("kind")
            if kind is not None and kind not in FILE_KINDS:
                reasons.append(f"ARCH_FILE_{i}_BAD_KIND:{kind}")

    reasons.extend(_check_evidence(data.get("evidence_ref")))

    if reasons:
        if fail_closed:
            raise ValidatorError("ARCH_REJECTED", ",".join(reasons))
        return {"ok": False, "reason_codes": reasons, "kind": "architecture_output"}
    return {"ok": True, "reason_codes": [], "kind": "architecture_output"}


def validate_code_output(data: Any, *, fail_closed: bool = True) -> dict[str, Any]:
    reasons: list[str] = []
    if not isinstance(data, dict):
        reasons.append("NOT_OBJECT")
        if fail_closed:
            raise ValidatorError("CODE_REJECTED", ",".join(reasons))
        return {"ok": False, "reason_codes": reasons, "kind": "code_output"}

    reasons.extend(_require(data, CODE_REQUIRED, "CODE"))
    if data.get("schema_version") not in (None, "1.0"):
        reasons.append(f"CODE_BAD_VERSION:{data.get('schema_version')}")

    lang = data.get("language")
    if lang is not None and lang not in LANGUAGES:
        reasons.append(f"CODE_BAD_LANGUAGE:{lang}")

    llm = data.get("llm_control")
    if llm is not None and llm != "DENY":
        reasons.append(f"CODE_LLM_NOT_DENY:{llm}")

    files = data.get("files")
    if not isinstance(files, list) or len(files) < 1:
        reasons.append("CODE_FILES_EMPTY")
    else:
        for i, item in enumerate(files):
            if not isinstance(item, dict):
                reasons.append(f"CODE_FILE_{i}_NOT_OBJECT")
                continue
            if "path" not in item or not item["path"]:
                reasons.append(f"CODE_FILE_{i}_NO_PATH")
            action = item.get("action")
            if action is not None and action not in FILE_ACTIONS:
                reasons.append(f"CODE_FILE_{i}_BAD_ACTION:{action}")

    reasons.extend(_check_evidence(data.get("evidence_ref")))

    if reasons:
        if fail_closed:
            raise ValidatorError("CODE_REJECTED", ",".join(reasons))
        return {"ok": False, "reason_codes": reasons, "kind": "code_output"}
    return {"ok": True, "reason_codes": [], "kind": "code_output"}


def validate_output(kind: str, data: Any, *, fail_closed: bool = True) -> dict[str, Any]:
    if kind == "architecture_output":
        return validate_architecture_output(data, fail_closed=fail_closed)
    if kind == "code_output":
        return validate_code_output(data, fail_closed=fail_closed)
    raise ValidatorError("UNKNOWN_KIND", kind)
