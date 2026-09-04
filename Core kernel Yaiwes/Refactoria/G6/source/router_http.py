"""Exact source snapshot for G6 refactoria.
Copied from extensions/wordflow_kernel/gateway/router_http.py.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .intelligence import GatewayRequest, GatewayResponse, MockIntelligenceGateway


class RouterHTTPGateway:
    def __init__(self, router_url: str | None = None, token_ref: str | None = None,
                 timeout_s: float = 30.0, allow_mock_fallback: bool = False,
                 path: str = "/api/router/execute") -> None:
        self.router_url = (router_url or os.environ.get("ROUTER_URL") or "").rstrip("/")
        self.token_ref = token_ref or os.environ.get("ROUTER_TOKEN_REF")
        self.timeout_s = timeout_s
        self.allow_mock_fallback = allow_mock_fallback
        self.path = path
        self._mock = MockIntelligenceGateway()

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        token = os.environ.get("ROUTER_TOKEN", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def execute(self, request: GatewayRequest) -> GatewayResponse:
        if not self.router_url:
            if self.allow_mock_fallback:
                return self._mock.execute(request)
            return GatewayResponse(request.request_id, request.task_id, request.trace_id, "DENY", {"reason": "ROUTER_URL_empty"}, None)
        url = f"{self.router_url}{self.path}"
        body = json.dumps(request.to_router_body()).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            return GatewayResponse(request.request_id, request.task_id, request.trace_id, "ERROR", {"reason": "http_error", "code": e.code}, "router_http")
        except Exception as e:
            if self.allow_mock_fallback:
                return self._mock.execute(request)
            return GatewayResponse(request.request_id, request.task_id, request.trace_id, "ERROR", {"reason": "network_error", "error": type(e).__name__}, "router_http")
        return GatewayResponse(str(data.get("request_id", request.request_id)), request.task_id, request.trace_id,
                               str(data.get("status", "OK")), dict(data.get("output") or data.get("result") or {}),
                               str(data.get("provider") or "router"), data.get("evidence_hash"))
