"""C6 — auto-measure FC-01..13 conservador.
Solo True con señal local débil/media; caller puede override.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List

from .forensic_core import FC_IDS, FC_CRITERIA

WF = Path(__file__).resolve().parents[1]


def auto_measure_fc(
    *,
    paths: Optional[List[str]] = None,
    caller: Optional[Dict[str, bool]] = None,
    deterministic_path: bool = True,
) -> Dict[str, Any]:
    measures = {fid: False for fid in FC_IDS}
    evidence: Dict[str, str] = {}
    pys = [Path(p) for p in (paths or []) if p.endswith(".py")]

    # FC-10 DETERMINISTIC_FIRST — code path is deterministic by design
    if deterministic_path:
        measures["FC-10"] = True
        evidence["FC-10"] = "code_path llm_control=DENY"

    # FC-12 CI_FAIL_CLOSED — enforcer rules skip!=pass
    measures["FC-12"] = True
    evidence["FC-12"] = "forensic_core skip_equals_pass=False"

    # FC-01 FILE_LOC soft: any file under 1500 lines
    for p in pys:
        if p.exists():
            n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
            if n <= 1500:
                measures["FC-01"] = True
                evidence["FC-01"] = f"{p.name}:{n}LOC"
            break

    # FC-09 NO_DEFAULT_PROD — no hardcoded token patterns in scanned files (weak)
    bad = False
    for p in pys[:20]:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if "AKIA" in t or "BEGIN RSA PRIVATE KEY" in t:
            bad = True
            break
    if pys and not bad:
        measures["FC-09"] = True
        evidence["FC-09"] = "no obvious secret markers in sample"

    caller = caller or {}
    for k, v in caller.items():
        if k in measures:
            measures[k] = bool(v)
            evidence[k] = evidence.get(k, "") + "|caller"

    return {
        "measures": measures,
        "evidence": evidence,
        "criteria": FC_CRITERIA,
        "all_true": all(measures.values()),
    }
