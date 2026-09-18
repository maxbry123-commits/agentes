"""Native TimesFM capability for the YAIWES kernel.

This module never downloads model weights. It routes temporal tasks to an
external TimesFM runtime and fails closed when that runtime is unavailable.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

CAP_FORECAST = "temporal.forecast"
CAP_ANOMALY = "temporal.anomaly_from_intervals"

TIMESFM_METHOD_MANIFEST: dict[str, Any] = {
    "id": "timesfm.external.temporal",
    "name": "TimesFM Native Temporal Capability",
    "version": "1.0.0",
    "capabilities": [CAP_FORECAST, CAP_ANOMALY],
    "inputs": ["series", "horizon", "related_series", "past_covariates", "future_covariates"],
    "outputs": ["point_forecast", "quantiles", "uncertainty", "metadata"],
    "contracts": ["forecast_is_evidence_not_direct_critical_action"],
    "quarantine": True,
    "tests_passed": False,
    "entry": "capabilities.timesfm_native:execute_native_capability",
    "meta": {
        "provider": "timesfm",
        "type": "external_ai_capability",
        "model_runtime_owner": "Router Inteligente Universal / AI Staff",
        "derived_capabilities": [CAP_ANOMALY],
    },
}

_TEMPORAL_TERMS = (
    "qué pasará", "que pasara", "pronóstico", "pronostico", "forecast",
    "proyectar", "proyección", "proyeccion", "tendencia", "demanda futura",
    "evolución temporal", "evolucion temporal", "próximos", "proximos",
    "series temporales", "predicción de métricas", "prediccion de metricas",
    "sensores", "carga futura", "tráfico futuro", "trafico futuro",
    "observabilidad temporal",
)

_PROGRAMMING_ONLY = (
    "escribe código", "escribe codigo", "programa una función", "programa una funcion",
    "refactoriza", "corrige este código", "corrige este codigo",
)


@dataclass(frozen=True)
class CapabilityDecision:
    selected: str | None
    provider: str | None
    reason: str
    derived_capability: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected": self.selected,
            "provider": self.provider,
            "reason": self.reason,
            "derived_capability": self.derived_capability,
        }


class CapabilityUnavailable(RuntimeError):
    pass


def _nested_temporal_flag(payload: Mapping[str, Any]) -> bool:
    if payload.get("task.requires_temporal_forecast") is True:
        return True
    task = payload.get("task")
    return isinstance(task, Mapping) and task.get("requires_temporal_forecast") is True


def _series_batches(payload: Mapping[str, Any]) -> list[list[float]]:
    raw = payload.get("series")
    if not isinstance(raw, list) or not raw:
        return []
    if all(isinstance(x, (int, float)) for x in raw):
        return [[float(x) for x in raw]]
    out: list[list[float]] = []
    for row in raw:
        if not isinstance(row, list) or not row:
            return []
        if not all(isinstance(x, (int, float)) for x in row):
            return []
        out.append([float(x) for x in row])
    return out


def has_sufficient_history(payload: Mapping[str, Any], min_points: int = 32) -> bool:
    batches = _series_batches(payload)
    return bool(batches) and all(len(row) >= min_points for row in batches)


def route_native_capability(task_text: str = "", payload: Mapping[str, Any] | None = None) -> CapabilityDecision:
    data = dict(payload or {})
    text = (task_text or str(data.get("query") or data.get("goal") or "")).strip().lower()
    explicit = _nested_temporal_flag(data)
    semantic = any(term in text for term in _TEMPORAL_TERMS)

    if not explicit and not semantic:
        return CapabilityDecision(None, None, "no_temporal_forecast_intent")

    if not explicit and any(term in text for term in _PROGRAMMING_ONLY):
        return CapabilityDecision(None, None, "programming_only_guard")

    if not has_sufficient_history(data):
        return CapabilityDecision(None, "timesfm", "insufficient_historical_observations")

    return CapabilityDecision(CAP_FORECAST, "timesfm", "temporal_forecast_required")


def register_timesfm(registry: Any) -> Any:
    """Register in YAIWES MethodRegistry while keeping the capability quarantined."""
    return registry.register(TIMESFM_METHOD_MANIFEST, source="google-research/timesfm")


class TimesFMAdapter:
    """Transport adapter for Router/API/MCP-proxy/local-service runtimes."""

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        mcp_endpoint: str | None = None,
        local_command: str | None = None,
        model_id: str | None = None,
        transport: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.endpoint = endpoint or os.getenv("TIMESFM_SERVICE_URL")
        self.mcp_endpoint = mcp_endpoint or os.getenv("TIMESFM_MCP_PROXY_URL")
        self.local_command = local_command or os.getenv("TIMESFM_LOCAL_COMMAND")
        self.model_id = model_id or os.getenv("TIMESFM_MODEL_ID", "google/timesfm-3.0-pytorch")
        self.transport = transport
        self.timeout_seconds = timeout_seconds

    @property
    def available(self) -> bool:
        return bool(self.transport or self.endpoint or self.mcp_endpoint or self.local_command)

    def _call_http(self, url: str, request: dict[str, Any], *, mcp_proxy: bool = False) -> Mapping[str, Any]:
        body: dict[str, Any] = request
        if mcp_proxy:
            body = {"method": "timesfm.forecast", "params": request}
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _call_command(self, request: dict[str, Any]) -> Mapping[str, Any]:
        argv = shlex.split(self.local_command or "")
        if not argv:
            raise CapabilityUnavailable("capability_unavailable")
        proc = subprocess.run(
            argv,
            input=json.dumps(request),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.timeout_seconds,
            check=False,
        )
        if proc.returncode != 0:
            raise CapabilityUnavailable("capability_unavailable")
        return json.loads(proc.stdout)

    def forecast(self, request: Mapping[str, Any]) -> dict[str, Any]:
        data = dict(request)
        if not has_sufficient_history(data):
            raise ValueError("insufficient_historical_observations")
        horizon = data.get("horizon")
        if not isinstance(horizon, int) or horizon <= 0:
            raise ValueError("horizon_must_be_positive_integer")
        data["capability"] = CAP_FORECAST
        data.setdefault("return_quantiles", True)

        if self.transport:
            raw = dict(self.transport(data))
        elif self.endpoint:
            raw = dict(self._call_http(self.endpoint, data))
        elif self.mcp_endpoint:
            raw = dict(self._call_http(self.mcp_endpoint, data, mcp_proxy=True))
            raw = dict(raw.get("result") or raw)
        elif self.local_command:
            raw = dict(self._call_command(data))
        else:
            raise CapabilityUnavailable("capability_unavailable")

        if "point_forecast" not in raw or "quantiles" not in raw:
            raise RuntimeError("timesfm_response_contract_invalid")

        return {
            "provider": "timesfm",
            "point_forecast": raw["point_forecast"],
            "quantiles": raw["quantiles"],
            "uncertainty": raw.get("uncertainty") or {"source": "quantile_intervals"},
            "metadata": {
                **dict(raw.get("metadata") or {}),
                "model": dict(raw.get("metadata") or {}).get("model", self.model_id),
                "capability": CAP_FORECAST,
                "decision_semantics": "evidence_only_not_direct_critical_action",
            },
        }


def anomaly_from_intervals(
    observations: Sequence[float],
    lower: Sequence[float],
    upper: Sequence[float],
) -> dict[str, Any]:
    if not (len(observations) == len(lower) == len(upper)):
        raise ValueError("interval_length_mismatch")
    flags = [
        {"index": i, "value": float(v), "anomaly": bool(v < lo or v > hi)}
        for i, (v, lo, hi) in enumerate(zip(observations, lower, upper))
    ]
    return {
        "capability": CAP_ANOMALY,
        "provider": "timesfm",
        "derived_capability": True,
        "items": flags,
        "anomaly_count": sum(1 for x in flags if x["anomaly"]),
    }


def execute_native_capability(
    task_text: str,
    payload: Mapping[str, Any],
    *,
    adapter: TimesFMAdapter | None = None,
) -> dict[str, Any]:
    decision = route_native_capability(task_text, payload)
    if decision.selected != CAP_FORECAST:
        reason = decision.reason
        status = "capability_unavailable" if reason == "insufficient_historical_observations" else "not_selected"
        return {"status": status, "decision": decision.to_dict()}

    runtime = adapter or TimesFMAdapter()
    if not runtime.available:
        return {
            "status": "capability_unavailable",
            "decision": decision.to_dict(),
            "provider": "timesfm",
        }

    try:
        result = runtime.forecast(payload)
    except CapabilityUnavailable:
        return {
            "status": "capability_unavailable",
            "decision": decision.to_dict(),
            "provider": "timesfm",
        }
    return {"status": "ok", "decision": decision.to_dict(), "result": result}
