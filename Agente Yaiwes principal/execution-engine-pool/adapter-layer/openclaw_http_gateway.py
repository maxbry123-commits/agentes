"""Canonical OpenClaw connection adapter.

Validated implementation copied from Refactoria/G7/new/openclaw_http_gateway.py.
The adapter is outside OpenClawEngine so future wiring does not require editing the engine.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from typing import Any

from wordflow_kernel.gateway.intelligence import GatewayRequest, GatewayResponse, IntelligenceGateway


class OpenClawHTTPGateway(IntelligenceGateway):
    """Fail-closed adapter for a private OpenClaw Gateway."""

    def __init__(self, base_url: str | None = None, token: str | None = None, timeout_s: float = 30.0) -> None:
        self.base_url = (base_url or os.environ.get("OPENCLAW_GATEWAY_URL") or "").rstrip("/")
        self.token = token or os.environ.get("OPENCLAW_GATEWAY_TOKEN") or ""
        self.timeout_s = timeout_s

    def _deny(self, request: GatewayRequest, reason: str) -> GatewayResponse:
        return GatewayResponse(request.request_id, request.task_id, request.trace_id, "DENY", {"reason": reason}, "openclaw")

    def execute(self, request: GatewayRequest) -> GatewayResponse:
        if request.capability != "llm.complete":
            return self._deny(request, f"unsupported_capability:{request.capability}")
        if not self.base_url:
            return self._deny(request, "OPENCLAW_GATEWAY_URL_empty")
        if not self.token:
            return self._deny(request, "OPENCLAW_GATEWAY_TOKEN_missing")
        messages = (request.payload or {}).get("messages")
        if not isinstance(messages, list) or not all(isinstance(m, dict) for m in messages):
            return self._deny(request, "messages_invalid")
        body = json.dumps({"model": "openclaw/default", "messages": messages, "stream": False,
                           "user": f"conv:{request.task_id}"}, separators=(",", ":")).encode()
        req = urllib.request.Request(f"{self.base_url}/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json", "Accept": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
                raw = response.read().decode("utf-8")
                data: dict[str, Any] = json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            return GatewayResponse(request.request_id, request.task_id, request.trace_id, "ERROR", {"reason": "http_error", "code": exc.code}, "openclaw")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return GatewayResponse(request.request_id, request.task_id, request.trace_id, "ERROR", {"reason": "network_error", "error": type(exc).__name__}, "openclaw")
        except (ValueError, TypeError) as exc:
            return GatewayResponse(request.request_id, request.task_id, request.trace_id, "ERROR", {"reason": "invalid_json", "error": type(exc).__name__}, "openclaw")
        choices = data.get("choices")
        text = ""
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                text = str(message.get("content") or "")
        if not text:
            return GatewayResponse(request.request_id, request.task_id, request.trace_id, "ERROR", {"reason": "openclaw_response_missing_text"}, "openclaw")
        return GatewayResponse(str(data.get("id") or request.request_id), request.task_id, request.trace_id,
            "OK", {"text": text}, "openclaw", hashlib.sha256(raw.encode()).hexdigest()[:16])

    def complete(self, prompt: str) -> str:
        response = self.execute(GatewayRequest("direct-complete", "direct-complete", "llm.complete",
            {"messages": [{"role": "user", "content": str(prompt)}]}))
        return str(response.output.get("text") or "")
