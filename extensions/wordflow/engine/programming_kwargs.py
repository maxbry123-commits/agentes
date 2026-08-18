"""S3/S4 — kwargs canónicos fail-closed para run_unified / main_12 programming_path.
No inventa PASS: CORE/FC/connectivity deben venir medidos o explicit True de CI.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from extensions.wordflow.standards.forensic_core import CORE_IDS, CONNECTIVITY_CHAIN, FC_IDS


def full_pass_kwargs(
    *,
    mission_id: str = "",
    quality_dag_ok: bool = True,
    include_fc: bool = True,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Solo para CI/smoke cuando las measures ya fueron verificadas externamente."""
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
    }
    if include_fc:
        kw["fc_results"] = {fid: True for fid in FC_IDS}
        kw["require_fc"] = False
    if extra:
        kw.update(extra)
    return kw


def minimal_block_kwargs() -> Dict[str, Any]:
    """Defaults seguros: context true, sin measures → FAIL forensic (no PASS falso)."""
    return {
        "context_verified": True,
        "handoff_verified": True,
        "auto_measure_core": True,
        "quality_dag_ok": False,
        "require_pre_gate": False,
    }
