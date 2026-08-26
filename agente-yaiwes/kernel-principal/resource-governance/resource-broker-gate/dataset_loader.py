"""DatasetLoader — PLAN_ONLY modes (no automatic bulk download)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contract import ResourceContract, AcquisitionMode


@dataclass
class DatasetPlan:
    mode: AcquisitionMode
    repo_id: str
    revision: str | None
    filename: str | None = None
    allow_patterns: tuple[str, ...] = ()
    streaming: bool = False
    note: str = "PLAN_ONLY — execute only when FETCH_ENABLED and policy allow"


class DatasetLoader:
    def plan(self, contract: ResourceContract, preferred: AcquisitionMode | None = None) -> DatasetPlan:
        mode = preferred or contract.acquisition_mode
        if mode == "auto":
            mode = "snapshot" if contract.kind == "dataset" else "file"
        if mode not in contract.allowed_modes and contract.allowed_modes:
            mode = contract.allowed_modes[0]
        repo_id = contract.resource_id.replace("hf://dataset/", "").replace("hf://", "")
        return DatasetPlan(
            mode=mode,  # type: ignore[arg-type]
            repo_id=repo_id,
            revision=contract.revision,
            filename=dict(contract.metadata).get("filename") if contract.metadata else None,
            streaming=(mode == "stream"),
        )

    def describe_execution(self, plan: DatasetPlan) -> dict[str, Any]:
        """Human/machine readable plan — does not download."""
        return {
            "action": f"dataset_{plan.mode}",
            "repo_id": plan.repo_id,
            "revision": plan.revision,
            "filename": plan.filename,
            "streaming": plan.streaming,
            "status": "PLAN_ONLY",
        }
