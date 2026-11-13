"""EVO.05 · software OS → KER package."""
from __future__ import annotations
from typing import Any
from ..pipeline import EvolutionMode, EvolutionRequest
from ..source_reuse import SourceReuseDecision

class ModeOsSource:
    mode = EvolutionMode.OS_SOURCE

    def run(self, req: EvolutionRequest, reuse: SourceReuseDecision) -> dict[str, Any]:
        if not reuse.sources_found and not reuse.allow_from_scratch:
            raise ValueError("os_source_requires_pinned_source")
        src = reuse.sources_found[0].to_dict() if reuse.sources_found else {}
        exports = list(req.payload.get("export_capabilities") or [])
        return {
            "candidate_id": f"os_{req.capability_id}",
            "package_path": f"extensions/os/{req.capability_id}",
            "evidence": {
                "mode": self.mode.value,
                "source": src,
                "export_capabilities": exports,
                "rule": "no_external_gui_required",
                "native_bus": True,
            },
        }
