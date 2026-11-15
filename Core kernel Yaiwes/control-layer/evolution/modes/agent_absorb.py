"""EVO.02 · agente → capability determinista."""
from __future__ import annotations
from typing import Any
from ..pipeline import EvolutionMode, EvolutionRequest
from ..source_reuse import SourceReuseDecision

class ModeAgentAbsorb:
    mode = EvolutionMode.AGENT_ABSORB

    def run(self, req: EvolutionRequest, reuse: SourceReuseDecision) -> dict[str, Any]:
        tools = list(req.payload.get("tools") or [])
        keep_llm = list(req.payload.get("llm_only_nodes") or ["code.generate"])
        capabilities = []
        for t in tools:
            name = t if isinstance(t, str) else str(t.get("name") or t.get("id") or "tool")
            capabilities.append({
                "id": f"absorbed.{req.capability_id}.{name}",
                "deterministic": name not in keep_llm,
                "origin_agent": req.source_hint,
            })
        return {
            "candidate_id": f"abs_{req.capability_id}",
            "package_path": f"extensions/absorbed/{req.capability_id}",
            "evidence": {
                "mode": self.mode.value,
                "capabilities": capabilities,
                "llm_only_nodes": keep_llm,
                "reuse": reuse.to_dict(),
            },
        }
