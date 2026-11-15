"""EVO.06 · dataset/acoplador → knowledge/work pack."""
from __future__ import annotations
from typing import Any
from ..pipeline import EvolutionMode, EvolutionRequest
from ..source_reuse import SourceReuseDecision

class ModeDataset:
    mode = EvolutionMode.DATASET

    def run(self, req: EvolutionRequest, reuse: SourceReuseDecision) -> dict[str, Any]:
        kind = str(req.payload.get("kind") or "knowledge_pack")
        version = str(req.payload.get("version") or "0.1.0")
        return {
            "candidate_id": f"pack_{req.capability_id}_{version}",
            "package_path": f"extensions/packs/{req.capability_id}/{version}",
            "evidence": {
                "mode": self.mode.value,
                "kind": kind,
                "version": version,
                "records_hint": int(req.payload.get("records_hint") or 0),
                "reuse": reuse.to_dict(),
                "rule": "versioned_pack_no_loose_prompts",
            },
        }
