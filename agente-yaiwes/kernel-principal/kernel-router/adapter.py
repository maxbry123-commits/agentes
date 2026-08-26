"""HTTP adapter to external Router Universal service.

Wordflow never selects vendor models itself — only posts RouteRequest.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .contracts import RouteRequest, RouteResponse
from wordflow_kernel.models import stable_hash


class RouterUniversalAdapter:
    def __init__(self, base_url: str | None = None, timeout: float = 60.0):
        self.base_url = (base_url or os.environ.get("ROUTER_URL", "")).rstrip("/")
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.base_url)

    def route(self, req: RouteRequest) -> RouteResponse:
        if not self.base_url:
            return RouteResponse(
                status="DENY",
                provider="none",
                output={"error": "ROUTER_URL not set"},
            )
        body = {
            "task_id": req.task_id,
            "trace_id": req.trace_id,
            "capability": req.capability,
            "payload": req.payload,
            "policy": req.policy,
        }
        data = json.dumps(body).encode()
        url = f"{self.base_url}/v1/route"
        http_req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_req, timeout=self.timeout) as resp:
                out = json.loads(resp.read().decode())
            return RouteResponse(
                status=str(out.get("status", "OK")),
                provider=str(out.get("provider", "router")),
                output=out.get("output") or out,
                evidence_hash=stable_hash(out),
            )
        except urllib.error.URLError as e:
            return RouteResponse(
                status="ERROR",
                provider="router",
                output={"error": str(e.reason)},
            )
