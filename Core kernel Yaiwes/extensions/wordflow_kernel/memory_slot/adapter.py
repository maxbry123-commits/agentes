"""MemoryOrchestratorAdapter — Wordflow never talks to Xata/Graphiti directly.

Path: Workflow → this adapter → ROUTER_URL memory capability OR local MemoryPort offline.
"""
from __future__ import annotations

import os
from typing import Any

from .contracts import MemoryRequest, MemoryResponse, MemoryCandidate
from wordflow_kernel.router_slot import RouterUniversalAdapter, RouteRequest


class MemoryOrchestratorAdapter:
    def __init__(self, router: RouterUniversalAdapter | None = None, local: Any = None):
        self.router = router or RouterUniversalAdapter()
        self.local = local  # MemoryPort optional offline

    def execute(self, req: MemoryRequest) -> MemoryResponse:
        if self.router.available():
            rr = self.router.route(
                RouteRequest(
                    task_id=req.task_id,
                    trace_id=req.trace_id,
                    capability=f"memory.{req.op}",
                    payload={
                        "query": req.query,
                        "item": req.item,
                        "scope": req.scope,
                    },
                    policy=req.policy,
                )
            )
            if rr.status in ("OK", "MOCK"):
                cands = [
                    MemoryCandidate(
                        content=str(c.get("content", "")),
                        score=float(c.get("score", 0)),
                        source=str(c.get("source", rr.provider)),
                    )
                    for c in (rr.output.get("candidates") or [])
                ]
                return MemoryResponse(status=rr.status, candidates=cands, detail=rr.output)
            return MemoryResponse(status=rr.status, detail=rr.output)

        if self.local is not None:
            if req.op == "store":
                self.local.store(req.item or {}, scope=req.scope)
                return MemoryResponse(status="OK", detail={"local": True})
            if req.op in ("search", "context"):
                rows = self.local.search(req.query or "", scope=req.scope)
                cands = [
                    MemoryCandidate(content=str(r), source="local") for r in rows[:20]
                ]
                return MemoryResponse(status="OK", candidates=cands, detail={"local": True})
            return MemoryResponse(status="OK", detail={"local": True, "op": req.op})

        return MemoryResponse(
            status="DENY",
            detail={"error": "no ROUTER_URL and no local MemoryPort"},
        )
