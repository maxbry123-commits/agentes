"""Deterministic authorization gate for generating new code.

Generation is a last resort after the reuse selector returns GENERATE.
This module never executes or deploys generated code and never lets an LLM
authorize its own output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

PLACEMENTS = {
    "A_KERNEL",
    "B_EXTENSION_KERNEL",
    "C_REASONING_LAYER",
    "D_WORDFLOW",
    "E_POOL",
    "F_TOOLS",
    "G_OTHER",
}


@dataclass(frozen=True)
class GenerationRequest:
    task_id: str
    capability: str
    reuse_decision: str
    placement: str
    target_path: str
    contract_id: str
    fables_binding: str
    provenance_ref: str
    requested_by_llm: bool = False


@dataclass(frozen=True)
class GenerationDecision:
    allowed: bool
    reason_codes: Tuple[str, ...]
    candidate_generation_allowed: bool
    execution_authorized: bool = False
    deployment_authorized: bool = False


def _safe_relative_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip()
    return (
        bool(normalized)
        and not normalized.startswith("/")
        and ".." not in normalized.split("/")
        and not normalized.startswith(".github/")
    )


def authorize_generation(req: GenerationRequest) -> GenerationDecision:
    missing = [
        name
        for name, value in (
            ("task_id", req.task_id),
            ("capability", req.capability),
            ("target_path", req.target_path),
            ("contract_id", req.contract_id),
            ("fables_binding", req.fables_binding),
            ("provenance_ref", req.provenance_ref),
        )
        if not str(value).strip()
    ]
    if missing:
        return GenerationDecision(
            False,
            ("MISSING_REQUIRED_FIELDS:" + ",".join(missing),),
            False,
        )
    if req.reuse_decision != "GENERATE":
        return GenerationDecision(False, ("REUSE_POLICY_NOT_GENERATE",), False)
    if req.placement not in PLACEMENTS:
        return GenerationDecision(False, ("PLACEMENT_NOT_APPROVED",), False)
    if not _safe_relative_path(req.target_path):
        return GenerationDecision(False, ("TARGET_PATH_NOT_AUTHORIZED_RELATIVE",), False)
    if req.fables_binding != "UNIVERSAL_PLUGIN_BUS":
        return GenerationDecision(False, ("FABLES_BINDING_REQUIRED",), False)

    reasons = [
        "REUSE_EXHAUSTED",
        "PLACEMENT_APPROVED",
        "CONTRACT_PRESENT",
        "FABLES_BINDING_DECLARED",
    ]
    if req.requested_by_llm:
        reasons.append("LLM_MAY_DRAFT_BUT_CANNOT_AUTHORIZE_EXECUTION")
    return GenerationDecision(True, tuple(reasons), True, False, False)
