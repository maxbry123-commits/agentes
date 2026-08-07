"""TencentAdapter · HTTP client al motor oficial · NO modifica source Tencent.

Endpoint tipico standalone: http://127.0.0.1:8420
Rutas: /health /capture /recall /v2/*
Si el servicio no está up → health degraded; capture/recall fallan controlado.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from typing import Any, List

from memory.schemas.context import MemoryContext, MemoryNamespace, MemoryRecord


class TencentAdapter:
    name = "tencent"

    def __init__(self, base_url: str = "http://127.0.0.1:8420", *, api_key: str = "", timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _req(self, method: str, path: str, body: dict | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8") or "{}"
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            return {"ok": False, "error": f"http_{e.code}", "detail": str(e)}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": "unreachable", "detail": str(e)}

    def health(self) -> dict[str, Any]:
        r = self._req("GET", "/health")
        if r.get("error"):
            return {"status": "degraded", "provider": self.name, **r}
        return {"status": "ok", "provider": self.name, "upstream": r}

    def capture(
        self,
        ctx: MemoryContext,
        content: str,
        *,
        type: str = "raw",
        meta: dict | None = None,
    ) -> MemoryRecord:
        ns = MemoryNamespace.from_context(ctx)
        payload = {
            "content": content,
            "type": type,
            "teamId": ctx.tenant_id,
            "agentId": ctx.agent_id,
            "userId": ctx.project_id,
            "sessionId": ctx.session_id,
            "namespace": ns.value,
            "meta": meta or {},
        }
        r = self._req("POST", "/capture", payload)
        mid = str(r.get("id") or r.get("node_id") or ("tc_" + hashlib.sha256(content.encode()).hexdigest()[:12]))
        return MemoryRecord(
            id=mid,
            content=content,
            type=type,
            namespace=ns.value,
            project_id=ctx.project_id,
            agent_id=ctx.agent_id,
            source="tencent",
            version=ctx.memory_version,
            meta={"upstream": r, **(meta or {})},
        )

    def recall(
        self,
        ctx: MemoryContext,
        query: str,
        *,
        top_n: int = 10,
    ) -> List[MemoryRecord]:
        ns = MemoryNamespace.from_context(ctx)
        payload = {
            "query": query,
            "limit": top_n,
            "teamId": ctx.tenant_id,
            "agentId": ctx.agent_id,
            "userId": ctx.project_id,
            "namespace": ns.value,
        }
        r = self._req("POST", "/recall", payload)
        items = r.get("items") or r.get("memories") or r.get("results") or []
        out: List[MemoryRecord] = []
        if isinstance(items, list):
            for i, it in enumerate(items[:top_n]):
                if not isinstance(it, dict):
                    continue
                out.append(
                    MemoryRecord(
                        id=str(it.get("id") or f"tc_r_{i}"),
                        content=str(it.get("content") or it.get("text") or ""),
                        type=str(it.get("type") or "semantic"),
                        namespace=ns.value,
                        project_id=ctx.project_id,
                        agent_id=ctx.agent_id,
                        source="tencent",
                        confidence=float(it.get("score") or it.get("confidence") or 0.5),
                        meta=it,
                    )
                )
        return out
