"""S3/S4/T1/T2 — kwargs canónicos fail-closed.
full_pass_kwargs REQUIERE ci_attestation=True (CI/smoke explícito).
Sin attestation → RuntimeError (no PASS silencioso en prod).
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from extensions.wordflow.standards.forensic_core import CORE_IDS, CONNECTIVITY_CHAIN, FC_IDS


def full_pass_kwargs(
    *,
    mission_id: str = "",
    quality_dag_ok: bool = True,
    include_fc: bool = True,
    ci_attestation: bool = False,
    attestation_source: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """CI/smoke only. ci_attestation must be True or raises."""
    if not ci_attestation:
        raise RuntimeError(
            "T1/T2 BLOCK: full_pass_kwargs requires ci_attestation=True "
            "(caller must have measured CORE/FC externally). "
            "Use minimal_block_kwargs() for safe defaults."
        )
    if not attestation_source:
        attestation_source = "unspecified_ci"
    kw: Dict[str, Any] = {
        "context_verified": True,
        "handoff_verified": True,
        "core_measures": {cid: True for cid in CORE_IDS},
        "connectivity": {k: True for k in CONNECTIVITY_CHAIN},
        "evidence_complete": True,
        "final_clean_reaudit_passed": True,
        "quality_dag_ok": quality_dag_ok,
        "mission_id": mission_id,
        "auto_measure_core": True,
        "auto_measure_fc": True,
        "require_pre_gate": False,
        "profile": "dev",
        "_ci_attestation": True,
        "_attestation_source": attestation_source,
    }
    if include_fc:
        kw["fc_results"] = {fid: True for fid in FC_IDS}
        kw["require_fc"] = False
    if extra:
        kw.update(extra)
    return kw


def minimal_block_kwargs() -> Dict[str, Any]:
    return {
        "context_verified": True,
        "handoff_verified": True,
        "auto_measure_core": True,
        "quality_dag_ok": False,
        "require_pre_gate": False,
        "_ci_attestation": False,
    }
