"""RouterHTTPGateway — production IntelligenceGateway via Router Universal FastAPI.

Loop never calls LLM vendors. This client only POSTs the stable contract body
to ROUTER_URL. If ROUTER_URL is empty or unreachable policy = fail_closed DENY
unless allow_mock_fallback=True (dev only).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .intelligence import (
    GatewayRequest,
    GatewayResponse,
    MockIntelligenceGateway,
)


class RouterHTTPGateway:
    def __init__(
        self,
        router_url: str | None = None,
        token_ref: str | None = None,
        timeout_s: float = 30.0,
        allow_mock_fallback: bool = False,
        path: str = "/api/router/execute",
    ) -> None:
        self.router_url = (router_url or os.environ.get("ROUTER_URL") or "").rstrip("/")
        self.token_ref = token_ref or os.environ.get("ROUTER_TOKEN_REF")
        self.timeout_s = timeout_s
        self.allow_mock_fallback = allow_mock_fallback
        self.path = path
        self._mock = MockIntelligenceGateway()

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        # Token resolved outside: only ref name travels in env; real secret injected by runtime
        token = os.environ.get("ROUTER_TOKEN", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def execute(self, request: GatewayRequest) -> GatewayResponse:
        if not self.router_url:
            if self.allow_mock_fallback:
                return self._mock.execute(request)
            return GatewayResponse(
                request_id=request.request_id,
                task_id=request.task_id,
                trace_id=request.trace_id,
                status="DENY",
                output={"reason": "ROUTER_URL_empty"},
                provider=None,
            )

        url = f"{self.router_url}{self.path}"
        body = json.dumps(request.to_router_body()).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            return GatewayResponse(
                request_id=request.request_id,
                task_id=request.task_id,
                trace_id=request.trace_id,
                status="ERROR",
                output={"reason": "http_error", "code": e.code, "body": e.read().decode("utf-8", errors="replace")[:500]},
                provider="router_http",
            )
        except Exception as e:  # noqa: BLE001 — boundary: network
            if self.allow_mock_fallback:
                return self._mock.execute(request)
            return GatewayResponse(
                request_id=request.request_id,
                task_id=request.task_id,
                trace_id=request.trace_id,
                status="ERROR",
                output={"reason": "network_error", "error": type(e).__name__},
                provider="router_http",
            )

        return GatewayResponse(
            request_id=str(data.get("request_id", request.request_id)),
            task_id=request.task_id,
            trace_id=request.trace_id,
            status=str(data.get("status", "OK")),
            output=dict(data.get("output") or data.get("result") or {}),
            provider=str(data.get("provider") or "router"),
            evidence_hash=data.get("evidence_hash"),
        )


def build_gateway_from_env() -> RouterHTTPGateway | MockIntelligenceGateway:
    """Factory: ROUTER_URL set → HTTP; else Mock."""
    url = os.environ.get("ROUTER_URL", "").strip()
    if not url:
        return MockIntelligenceGateway()
    return RouterHTTPGateway(
        router_url=url,
        allow_mock_fallback=os.environ.get("ROUTER_MOCK_FALLBACK", "false").lower() == "true",
    )
