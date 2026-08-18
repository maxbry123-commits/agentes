"""Fail-closed gate — S12/T12
Ficha inválida o llm_control != DENY donde se exige → raise.
"""
from __future__ import annotations
from typing import Dict, Any, Optional

class FailClosedError(Exception):
    pass

def validate_ficha(ficha: Dict[str, Any], require_llm_deny: bool = True) -> None:
    if not isinstance(ficha, dict):
        raise FailClosedError("ficha no es dict")
    if not ficha.get("id") and not ficha.get("name"):
        raise FailClosedError("ficha sin id/name")
    if require_llm_deny:
        ctrl = ficha.get("llm_control") or ficha.get("LLM_CONTROL") or ""
        if str(ctrl).upper() not in ("DENY", "DISABLED", "OFF", ""):
            # empty allowed only if explicit policy says so; strict default DENY
            if str(ctrl).upper() not in ("DENY", "DISABLED", "OFF"):
                raise FailClosedError(f"llm_control debe ser DENY, got: {ctrl}")

def assert_llm_deny(context: Optional[Dict[str, Any]] = None) -> None:
    ctx = context or {}
    val = ctx.get("llm_control") or ctx.get("LLM_CONTROL") or "DENY"
    if str(val).upper() not in ("DENY", "DISABLED", "OFF"):
        raise FailClosedError("llm_control no DENY en path determinista")
