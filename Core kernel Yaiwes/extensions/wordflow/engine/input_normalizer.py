# -*- coding: utf-8 -*-
"""InputBlock normalizer — A-WF-01. 0% LLM. Literal read + validate."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SOURCE_TYPES = frozenset({"chat", "document", "file", "system", "repair"})
QUALITY_BARS = frozenset({"never_MVP", "standard", "draft"})
PRIORITIES = frozenset({"P0", "P1", "P2", "P3"})
SECRET_RE = re.compile(
    r"(token|api[_-]?key|password|bearer|ghp_|github_pat_)",
    re.IGNORECASE,
)

REASON = {
    "MISSING_BLOCK": "MISSING_BLOCK",
    "INVALID_SCHEMA": "INVALID_SCHEMA",
    "MISSING_FIELD": "MISSING_FIELD",
    "EMPTY_RAW_TEXT": "EMPTY_RAW_TEXT",
    "SECRET_IN_INPUT": "SECRET_IN_INPUT",
    "INVALID_QUALITY_BAR": "INVALID_QUALITY_BAR",
    "INVALID_SOURCE_TYPE": "INVALID_SOURCE_TYPE",
}


class InputBlockError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _require(obj: dict, key: str) -> Any:
    if key not in obj or obj[key] is None or obj[key] == "":
        raise InputBlockError(REASON["MISSING_FIELD"], key)
    return obj[key]


def _scan_secrets(obj: Any, path: str = "root") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if SECRET_RE.search(str(k)):
                raise InputBlockError(REASON["SECRET_IN_INPUT"], f"key:{path}.{k}")
            _scan_secrets(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _scan_secrets(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        if SECRET_RE.search(obj) and not obj.startswith("http"):
            raise InputBlockError(REASON["SECRET_IN_INPUT"], path)


def normalize_input_block(raw: dict[str, Any] | None) -> dict[str, Any]:
    if raw is None or not isinstance(raw, dict):
        raise InputBlockError(REASON["MISSING_BLOCK"])

    _scan_secrets(raw)

    schema_version = _require(raw, "schema_version")
    if schema_version != "1.0":
        raise InputBlockError(REASON["INVALID_SCHEMA"], f"schema_version={schema_version}")

    block_id = str(_require(raw, "block_id"))
    source_type = _require(raw, "source_type")
    if source_type not in SOURCE_TYPES:
        raise InputBlockError(REASON["INVALID_SOURCE_TYPE"], str(source_type))

    raw_text = _require(raw, "raw_text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise InputBlockError(REASON["EMPTY_RAW_TEXT"])

    quality_bar = _require(raw, "quality_bar")
    if quality_bar not in QUALITY_BARS:
        raise InputBlockError(REASON["INVALID_QUALITY_BAR"], str(quality_bar))

    goals_hint = raw.get("goals_hint")
    if goals_hint is None:
        raise InputBlockError(REASON["MISSING_FIELD"], "goals_hint")
    if not isinstance(goals_hint, list):
        raise InputBlockError(REASON["INVALID_SCHEMA"], "goals_hint must be list")

    priority = raw.get("priority") or "P1"
    if priority not in PRIORITIES:
        raise InputBlockError(REASON["INVALID_SCHEMA"], f"priority={priority}")

    block: dict[str, Any] = {
        "schema_version": "1.0",
        "block_id": block_id,
        "source_type": source_type,
        "raw_text": raw_text.strip(),
        "quality_bar": quality_bar,
        "goals_hint": [str(g) for g in goals_hint],
        "priority": priority,
        "parent_block_id": raw.get("parent_block_id"),
        "doc_refs": list(raw.get("doc_refs") or []),
        "constraints": dict(raw.get("constraints") or {}),
        "meta": dict(raw.get("meta") or {}),
    }

    block["flags"] = {
        "never_mvp": quality_bar == "never_MVP",
        "is_repair": source_type == "repair",
        "has_parent": bool(block["parent_block_id"]),
    }

    canonical = json.dumps(
        {k: v for k, v in block.items() if k != "flags"},
        sort_keys=True,
        separators=(",", ":"),
    )
    block["block_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return block


def validate_or_reason(raw: dict[str, Any] | None) -> tuple[bool, dict[str, Any]]:
    try:
        return True, normalize_input_block(raw)
    except InputBlockError as e:
        return False, {"ok": False, "reason_code": e.reason_code, "detail": e.detail}
