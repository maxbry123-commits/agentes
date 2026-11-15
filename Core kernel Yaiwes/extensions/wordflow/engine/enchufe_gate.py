# -*- coding: utf-8 -*-
"""Enchufe gate C-02 — validate ficha.v2 before load. 0% LLM. llm_control DENY."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "artifact_id",
    "abi_version",
    "extension_type",
    "kernel_min",
    "mount_mode",
    "load_priority",
    "llm_control",
)

ALLOWED_LLM = {"DENY"}


class EnchufeGateError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _load_ficha(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise EnchufeGateError("FICHA_MISSING", str(path))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EnchufeGateError("FICHA_INVALID_JSON", str(exc)) from exc
    if not isinstance(data, dict):
        raise EnchufeGateError("FICHA_NOT_OBJECT", type(data).__name__)
    return data


def validate_ficha(data: dict[str, Any]) -> dict[str, Any]:
    """Return {ok, reason_codes, ficha}. Fail-closed on missing/DENY."""
    reasons: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            reasons.append(f"MISSING_{field}")
    llm = data.get("llm_control")
    if llm is not None and llm not in ALLOWED_LLM:
        reasons.append(f"LLM_NOT_DENY:{llm}")
    if data.get("llm_control") is None and "MISSING_llm_control" not in reasons:
        reasons.append("MISSING_llm_control")
    if reasons:
        return {"ok": False, "reason_codes": reasons, "ficha": data}
    return {"ok": True, "reason_codes": [], "ficha": data}


def load_and_validate(module_root: str | Path) -> dict[str, Any]:
    """Locate ficha.v2.json under module_root and validate."""
    root = Path(module_root)
    ficha_path = root / "ficha.v2.json"
    data = _load_ficha(ficha_path)
    result = validate_ficha(data)
    result["path"] = str(ficha_path)
    if not result["ok"]:
        raise EnchufeGateError("FICHA_REJECTED", ",".join(result["reason_codes"]))
    return result


def gate_load(module_root: str | Path) -> dict[str, Any]:
    """Public entry: PASS dict or raise EnchufeGateError."""
    return load_and_validate(module_root)
