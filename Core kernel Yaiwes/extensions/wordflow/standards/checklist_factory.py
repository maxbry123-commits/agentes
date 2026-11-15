"""S6/T6 — AgentChecklistClaim desde dict. Sin evidence placeholder."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from .checklist_sheriff import AgentChecklistClaim, PointClaim
from .programming_points_catalog import CATALOG_VERSION, core_ids


def checklist_from_dict(data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> AgentChecklistClaim:
    d = dict(data or {})
    d.update(kwargs)
    claims_in = d.get("claims") or []
    claims: List[PointClaim] = []
    for c in claims_in:
        if isinstance(c, PointClaim):
            claims.append(c)
        elif isinstance(c, dict):
            claims.append(
                PointClaim(
                    point_id=str(c.get("point_id", "")),
                    addressed=bool(c.get("addressed", False)),
                    evidence=str(c.get("evidence", "")),
                    evidence_kind=str(c.get("evidence_kind", "measure")),
                    skipped_reason=str(c.get("skipped_reason", "")),
                )
            )
    # T6: auto_core_claims requires real evidence string from caller — no placeholder
    if not claims and d.get("auto_core_claims"):
        ev = str(d.get("auto_core_evidence", "")).strip()
        if not ev or "placeholder" in ev.lower():
            # leave claims empty → Sheriff FAIL required missing (fail-closed)
            claims = []
        else:
            for pid in core_ids():
                claims.append(PointClaim(point_id=pid, addressed=True, evidence=ev, evidence_kind="measure"))
    return AgentChecklistClaim(
        mission_id=str(d.get("mission_id", "mission-local")),
        task_id=str(d.get("task_id", "task-local")),
        catalog_version=str(d.get("catalog_version", CATALOG_VERSION)),
        action=str(d.get("action", "GENERATE")),
        sources=list(d.get("sources") or []),
        files_touched=list(d.get("files_touched") or []),
        claims=claims,
        proposed_non_applicable=list(d.get("proposed_non_applicable") or []),
        tags_hint=dict(d.get("tags_hint") or {}),
    )
