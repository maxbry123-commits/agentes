# -*- coding: utf-8 -*-
"""C-28 Adapter contracts — Capability + Engine. Kernel never knows concrete engines. 0% LLM."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class AdapterError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


@runtime_checkable
class CapabilityAdapter(Protocol):
    adapter_id: str
    capability: str

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]: ...


@runtime_checkable
class EngineAdapter(Protocol):
    engine_id: str
    engine_kind: str

    def execute(self, task: dict[str, Any]) -> dict[str, Any]: ...


def validate_capability_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise AdapterError("CAP_RESULT_NOT_OBJECT")
    if "ok" not in result:
        raise AdapterError("CAP_RESULT_MISSING_OK")
    return {
        "ok": bool(result.get("ok")),
        "reason_codes": list(result.get("reason_codes") or []),
        "data": result.get("data"),
        "llm_control": "DENY",
    }


def validate_engine_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise AdapterError("ENG_RESULT_NOT_OBJECT")
    if "ok" not in result:
        raise AdapterError("ENG_RESULT_MISSING_OK")
    if "status" not in result:
        raise AdapterError("ENG_RESULT_MISSING_STATUS")
    status = result.get("status")
    if status not in ("SUCCESS", "FAILED", "SKIPPED", "DENIED"):
        raise AdapterError("ENG_BAD_STATUS", str(status))
    return {
        "ok": bool(result.get("ok")),
        "status": status,
        "reason_codes": list(result.get("reason_codes") or []),
        "artifacts": list(result.get("artifacts") or []),
        "llm_control": "DENY",
    }


class StaticCapabilityAdapter:
    """Deterministic capability stub (no network)."""

    def __init__(self, adapter_id: str, capability: str, *,
                 ok: bool = True, data: dict[str, Any] | None = None):
        self.adapter_id = adapter_id
        self.capability = capability
        self._ok = ok
        self._data = dict(data or {})

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_capability_result({
            "ok": self._ok,
            "reason_codes": [] if self._ok else ["CAP_DENIED"],
            "data": {**self._data, "payload_keys": sorted(payload.keys())},
        })


class StaticEngineAdapter:
    """Deterministic engine stub — never embedded OpenClaw/Hermes."""

    def __init__(self, engine_id: str, engine_kind: str = "stub",
                 *, ok: bool = True, status: str = "SUCCESS"):
        self.engine_id = engine_id
        self.engine_kind = engine_kind
        self._ok = ok
        self._status = status

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        return validate_engine_result({
            "ok": self._ok,
            "status": self._status if self._ok else "FAILED",
            "reason_codes": [] if self._ok else ["ENGINE_STUB_FAIL"],
            "artifacts": [{"task_id": task.get("task_id"), "engine": self.engine_id}],
        })
