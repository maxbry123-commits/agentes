"""EVO.03 · descapitar + micro TEAM."""
from __future__ import annotations
from typing import Any
from ..pipeline import EvolutionMode, EvolutionRequest
from ..source_reuse import SourceReuseDecision

class ModeDecapitate:
    mode = EvolutionMode.DECAPITATE

    def run(self, req: EvolutionRequest, reuse: SourceReuseDecision) -> dict[str, Any]:
        remove = list(req.payload.get("remove_modules") or ["planner", "agent_loop", "free_tool_router"])
        keep = list(req.payload.get("keep_modules") or ["tools", "workers", "ui", "mcp", "sessions"])
        entrypoint = str(req.payload.get("entrypoint") or "control_layer.team_entrypoint")
        return {
            "candidate_id": f"decap_{req.capability_id}",
            "package_path": f"extensions/decapitated/{req.capability_id}",
            "evidence": {
                "mode": self.mode.value,
                "remove": remove,
                "keep": keep,
                "new_entrypoint": entrypoint,
                "host": req.source_hint,
                "reuse": reuse.to_dict(),
            },
        }
