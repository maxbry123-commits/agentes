"""Fail-closed gate — T12

Ficha inválida o llm_control != DENY donde se exige → FailClosedError.
ADAPT: usa validate_ficha de T10 (artifact_id|id|name + abi_version|version).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .ficha_loader import validate_ficha as t10_validate_ficha

_DENY_VALUES = frozenset({"DENY", "DISABLED", "OFF"})
_LAST_REASON: Optional[str] = None


class FailClosedError(Exception):
    """Sistema cierra: no seguir como si fuera OK."""


def last_reason() -> Optional[str]:
    return _LAST_REASON


def fail_closed(reason: str) -> None:
    global _LAST_REASON
    _LAST_REASON = str(reason)
    raise FailClosedError(reason)


def _llm_control_value(ficha: Dict[str, Any]) -> Optional[str]:
    if "llm_control" not in ficha and "LLM_CONTROL" not in ficha:
        return None
    raw = ficha.get("llm_control", ficha.get("LLM_CONTROL"))
    return str(raw).upper() if raw is not None else ""


def assert_ficha_or_fail(ficha: dict, require_llm_deny: bool = True) -> dict:
    if not isinstance(ficha, dict):
        fail_closed("ficha no es dict")
    errors = t10_validate_ficha(ficha)
    if errors:
        fail_closed("ficha inválida: " + "; ".join(errors))
    ctrl = _llm_control_value(ficha)
    if require_llm_deny and ctrl is not None and ctrl not in _DENY_VALUES:
        fail_closed(f"llm_control debe ser DENY, got: {ctrl}")
    return ficha


def validate_ficha(ficha: Dict[str, Any], require_llm_deny: bool = True) -> None:
    """Compat: raise FailClosedError si inválida."""
    assert_ficha_or_fail(ficha, require_llm_deny=require_llm_deny)


def assert_llm_deny(context: Optional[Dict[str, Any]] = None) -> None:
    ctx = context or {}
    val = ctx.get("llm_control") or ctx.get("LLM_CONTROL") or "DENY"
    if str(val).upper() not in _DENY_VALUES:
        fail_closed("llm_control no DENY en path determinista")


if __name__ == "__main__":
    import json
    from pathlib import Path

    raised = False
    try:
        assert_ficha_or_fail({"abi_version": "2.0"})
    except FailClosedError as exc:
        raised = True
        assert "identifier" in str(exc) or "inválida" in str(exc)
    if not raised:
        raise SystemExit("FAIL: ficha sin id debía fallar")

    real = json.loads((Path(__file__).resolve().parent / "ficha.v2.json").read_text(encoding="utf-8"))
    out = assert_ficha_or_fail(real)
    assert out["artifact_id"] == "wordflow.kernel.extension"

    raised = False
    try:
        assert_ficha_or_fail(
            {"artifact_id": "x", "abi_version": "2.0", "llm_control": "ALLOW"}
        )
    except FailClosedError:
        raised = True
    if not raised:
        raise SystemExit("FAIL: llm_control ALLOW debía fallar")

    print("ok fail_closed")
