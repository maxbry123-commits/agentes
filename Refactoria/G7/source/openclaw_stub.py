"""OpenClaw EngineAdapter — reasoning intermediate stub (V1).

Not a continuous loop controller. Not a deploy motor.
When fully wired, OpenClaw structures the reasoning prompt; LLM goes via Gateway→Router.
"""
from __future__ import annotations

from wordflow_kernel.gateway.intelligence import IntelligenceGateway, make_request
from .port import EngineRequest, EngineResult


class OpenClawEngine:
    engine_id = "openclaw"

    def reason(self, request: EngineRequest, gateway: IntelligenceGateway) -> EngineResult:
        # Structure intermediate reasoning envelope (deterministic)
        envelope = {
            "role": "openclaw_reasoner",
            "task_id": request.task_id,
            "messages": request.messages,
            "context_keys": sorted(request.context.keys()),
        }
        gw_req = make_request(
            task_id=request.task_id,
            capability="llm.complete",
            payload={"messages": request.messages, "engine": self.engine_id, "envelope": envelope},
            trace_id=request.trace_id,
            policy=request.policy,
        )
        gw_res = gateway.execute(gw_req)
        if gw_res.status in ("DENY", "ERROR"):
            return EngineResult(
                engine_id=self.engine_id,
                status=gw_res.status,
                content="",
                meta={"gateway": gw_res.status, "output": gw_res.output},
            )
        text = str(gw_res.output.get("text", ""))
        return EngineResult(
            engine_id=self.engine_id,
            status="STUB" if gw_res.status == "MOCK" else "OK",
            content=text,
            meta={"provider": gw_res.provider, "evidence_hash": gw_res.evidence_hash},
        )
