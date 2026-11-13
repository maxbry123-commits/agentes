"""Null the workflow pointers whose session no longer exists.

A pointer to a missing thing is worse than no pointer at all. The UI reads `edit_agent_session_id`,
asks for a session that is gone, gets nothing back, and renders a blank panel with no explanation.
No pointer renders the designed empty state instead, which is the thing a user can actually read.

This runs once at boot. It cannot recover a deleted transcript, and it is not a substitute for
never losing one; it is the wall that keeps a loss from showing up as a broken-looking screen.
"""

import logging
from typing import Dict, List

from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

from backend.apps.workflows import storage
from backend.apps.workflows.owned_sessions import OWNED_SESSION_FIELDS

logger = logging.getLogger(__name__)


class ReconcileReport(BaseModel):
    """What the sweep found, so a silent heal still leaves a trace worth reading."""

    model_config = ConfigDict(validate_assignment=True)

    workflows_scanned: int = 0
    pointers_cleared: int = 0
    workflows_touched: List[str] = []


@typechecked
def reconcile_workflow_sessions() -> ReconcileReport:
    """Clear sticky session pointers whose file is gone. Safe to run repeatedly."""
    from backend.apps.agents.manager.session.session_store import load_session_data

    report = ReconcileReport()
    resolved: Dict[str, bool] = {}
    # Trashed ones too, or restoring a workflow hands the user back a pointer that already dangles.
    for wf in list(storage.list_workflows()) + list(storage.list_deleted_workflows()):
        report.workflows_scanned += 1
        dirty = False
        for field in OWNED_SESSION_FIELDS:
            sid = getattr(wf, field, None)
            if not isinstance(sid, str) or not sid:
                continue
            if sid not in resolved:
                try:
                    resolved[sid] = load_session_data(sid) is not None
                except Exception:
                    # Unreadable is not the same as missing; leave the pointer rather than guess.
                    resolved[sid] = True
            if resolved[sid]:
                continue
            setattr(wf, field, None)
            report.pointers_cleared += 1
            dirty = True
        if dirty:
            report.workflows_touched.append(wf.id)
            storage.save_workflow(wf)
    if report.pointers_cleared:
        logger.info(
            "reconcile: cleared %d dangling session pointer(s) across %d of %d workflow(s)",
            report.pointers_cleared, len(report.workflows_touched), report.workflows_scanned,
        )
    return report
