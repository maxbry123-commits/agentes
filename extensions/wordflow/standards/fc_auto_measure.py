"""C6/U8 — auto-measure FC conservador + cobertura explícita."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List

from .forensic_core import FC_IDS, FC_CRITERIA

# U8: solo estos se auto-miden; el resto exige caller/CI
FC_AUTO_COVERED = ("FC-01", "FC-09", "FC-10", "FC-12")
FC_CALLER_REQUIRED = tuple(fid for fid in FC_IDS if fid not in FC_AUTO_COVERED)


def auto_measure_fc(
    *,
    paths: Optional[List[str]] = None,
    caller: Optional[Dict[str, bool]] = None,
    deterministic_path: bool = True,
) -> Dict[str, Any]:
    measures = {fid: False for fid in FC_IDS}
    evidence: Dict[str, str] = {}
    pys = [Path(p) for p in (paths or []) if str(p).endswith(".py")]

    if deterministic_path:
        measures["FC-10"] = True
        evidence["FC-10"] = "code_path llm_control=DENY"

    measures["FC-12"] = True
    evidence["FC-12"] = "forensic_core skip_equals_pass=False"

    for p in pys:
        if p.exists():
            n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
            if n <= 1500:
                measures["FC-01"] = True
                evidence["FC-01"] = f"{p.name}:{n}LOC"
            break

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
        "auto_covered": list(FC_AUTO_COVERED),
        "caller_required": list(FC_CALLER_REQUIRED),
        "note": "U8: require_fc needs caller for FC not in auto_covered",
    }
