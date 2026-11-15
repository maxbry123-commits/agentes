# -*- coding: utf-8 -*-
"""InputCompiler — T0a. 0% LLM. Literal compile raw/input_block → InputContract."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any

from .input_normalizer import (
    InputBlockError,
    normalize_input_block,
    validate_or_reason,
)

REQUIRED_FOR_COMPLETE = (
    "objective",
    "success_criteria",
)

RISK_WORDS = {
    "high": ("delete", "drop", "production", "prod", "secret", "credential", "force"),
    "medium": ("write", "push", "deploy", "migrate", "modify"),
}

OBJECTIVE_RE = re.compile(
    r"(?:^|\n)\s*(?:objective|objetivo|goal)\s*[:\-]\s*(.+)",
    re.IGNORECASE,
)
SUCCESS_RE = re.compile(
    r"(?:^|\n)\s*(?:success|éxito|criterio(?: de éxito)?)\s*[:\-]\s*(.+)",
    re.IGNORECASE,
)
CONSTRAINT_RE = re.compile(
    r"(?:^|\n)\s*(?:constraint|restricci[oó]n|constraints)\s*[:\-]\s*(.+)",
    re.IGNORECASE,
)
FORBIDDEN_RE = re.compile(
    r"(?:^|\n)\s*(?:forbidden|prohibid[oa]s?)\s*[:\-]\s*(.+)",
    re.IGNORECASE,
)
ROLLBACK_RE = re.compile(
    r"(?:^|\n)\s*(?:rollback|reversi[oó]n)\s*[:\-]\s*(.+)",
    re.IGNORECASE,
)


def _line_values(pattern: re.Pattern[str], text: str) -> list[str]:
    return [m.group(1).strip() for m in pattern.finditer(text) if m.group(1).strip()]


def _first(pattern: re.Pattern[str], text: str) -> str:
    vals = _line_values(pattern, text)
    return vals[0] if vals else ""


def _guess_risk(text: str) -> str:
    low = text.lower()
    for level, words in RISK_WORDS.items():
        if any(w in low for w in words):
            return level
    return "unknown"


def _split_list(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[,;|]" , value)
    return [p.strip() for p in parts if p.strip()]


def _hash_contract(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compile_input_contract(
    raw: dict[str, Any] | str | None,
    *,
    contract_id: str | None = None,
) -> dict[str, Any]:
    """Compile InputContract from input_block dict or raw string. No LLM."""
    if isinstance(raw, str):
        block_raw = {
            "schema_version": "1.0",
            "block_id": f"blk_{uuid.uuid4().hex[:12]}",
            "source_type": "chat",
            "raw_text": raw,
            "quality_bar": "never_MVP",
            "goals_hint": [],
            "priority": "P1",
        }
    elif isinstance(raw, dict):
        block_raw = raw
    else:
        raise InputBlockError("MISSING_BLOCK", "raw is None")

    block = normalize_input_block(block_raw)
    text = block["raw_text"]

    objective = _first(OBJECTIVE_RE, text)
    if not objective and block.get("goals_hint"):
        objective = str(block["goals_hint"][0])

    success = _first(SUCCESS_RE, text)
    constraints = []
    for c in _line_values(CONSTRAINT_RE, text):
        constraints.extend(_split_list(c))
    forbidden = []
    for f in _line_values(FORBIDDEN_RE, text):
        forbidden.extend(_split_list(f))
    rollback = _first(ROLLBACK_RE, text)

    missing: list[str] = []
    if not objective:
        missing.append("objective")
    if not success:
        missing.append("success_criteria")

    status = "COMPLETE" if not missing else "INCOMPLETE"

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "contract_id": contract_id or f"ic_{uuid.uuid4().hex[:12]}",
        "source": {
            "source_type": block["source_type"],
            "block_id": block["block_id"],
            "block_hash": block.get("block_hash"),
            "doc_refs": list(block.get("doc_refs") or []),
        },
        "raw_literal": text,
        "objective": objective,
        "expected_result": "",
        "constraints": constraints,
        "forbidden": forbidden,
        "success_criteria": success,
        "rollback": rollback,
        "resources_declared": [],
        "engines_allowed": [],
        "risk_level": _guess_risk(text),
        "priority": block.get("priority") or "P1",
        "budget": {"tokens": None, "time_s": None, "cost": None},
        "timeout_s": None,
        "approver": "unknown",
        "literal_mode": True,
        "status": status,
        "missing_fields": missing,
        "flags": {
            "never_mvp": bool(block.get("flags", {}).get("never_mvp")),
            "is_repair": bool(block.get("flags", {}).get("is_repair")),
            "has_secrets_scan_pass": True,
        },
    }
    body["contract_hash"] = _hash_contract(
        {k: v for k, v in body.items() if k != "contract_hash"}
    )
    return body


def compile_or_reason(
    raw: dict[str, Any] | str | None,
) -> tuple[bool, dict[str, Any]]:
    """Compile or reason from a normalized input block."""
    ok, block_or_err = validate_or_reason(
        raw
        if isinstance(raw, dict)
        else {
            "schema_version": "1.0",
            "block_id": f"blk_{uuid.uuid4().hex[:12]}",
            "source_type": "chat",
            "raw_text": raw or "",
            "quality_bar": "never_MVP",
            "goals_hint": [],
        }
        if isinstance(raw, str)
        else None
    )
    if not ok:
        return False, block_or_err
    try:
        contract = compile_input_contract(block_or_err if isinstance(raw, dict) else raw)
        return True, contract
    except InputBlockError as e:
        return False, {"ok": False, "reason_code": e.reason_code, "detail": e.detail}
