# -*- coding: utf-8 -*-
"""C-04 Dual compiler — routes knowledge vs code outputs; promote_12 seed. 0% LLM."""
from __future__ import annotations

import re
from typing import Any

from .validator import ValidatorError, validate_architecture_output, validate_code_output

SHA40 = re.compile(r"^[0-9a-f]{40}$")


class DualCompilerError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def check_version_pin(pin: str | None) -> dict[str, Any]:
    if not pin:
        return {"ok": False, "reason": "PIN_MISSING"}
    if not SHA40.match(pin):
        return {"ok": False, "reason": "PIN_NOT_SHA40", "pin": pin}
    return {"ok": True, "pin": pin}


def compile_output(
    kind: str,
    payload: dict[str, Any],
    *,
    version_pin: str | None = None,
    require_pin: bool = False,
) -> dict[str, Any]:
    """kind: knowledge|architecture_output|code_output"""
    kind = (kind or "").lower()
    if require_pin:
        vp = check_version_pin(version_pin)
        if not vp["ok"]:
            raise DualCompilerError(vp["reason"], str(version_pin))

    if kind in ("architecture_output", "knowledge", "arch"):
        try:
            v = validate_architecture_output(payload, fail_closed=True)
        except ValidatorError as e:
            raise DualCompilerError(e.reason_code, e.detail) from e
        return {
            "ok": True,
            "track": "knowledge",
            "validation": v,
            "version_pin": version_pin,
            "llm_control": "DENY",
        }

    if kind in ("code_output", "code"):
        try:
            v = validate_code_output(payload, fail_closed=True)
        except ValidatorError as e:
            raise DualCompilerError(e.reason_code, e.detail) from e
        return {
            "ok": True,
            "track": "code",
            "validation": v,
            "version_pin": version_pin,
            "llm_control": "DENY",
        }

    raise DualCompilerError("UNKNOWN_TRACK", kind)


def promote_12(
    *,
    package_id: str,
    track: str,
    version_pin: str,
    license: str = "MIT",
    evidence_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministic promote gate — does not write remote; returns promote ticket."""
    vp = check_version_pin(version_pin)
    if not vp["ok"]:
        return {"ok": False, "reason_codes": [vp["reason"]], "llm_control": "DENY"}
    if track not in ("knowledge", "code"):
        return {"ok": False, "reason_codes": ["BAD_TRACK"], "llm_control": "DENY"}
    if not package_id:
        return {"ok": False, "reason_codes": ["PACKAGE_ID_EMPTY"], "llm_control": "DENY"}

    return {
        "ok": True,
        "promoted": True,
        "package_id": package_id,
        "track": track,
        "version_pin": version_pin,
        "license": license,
        "evidence_ref": dict(evidence_ref or {}),
        "status": "AVAILABLE",
        "llm_control": "DENY",
    }
