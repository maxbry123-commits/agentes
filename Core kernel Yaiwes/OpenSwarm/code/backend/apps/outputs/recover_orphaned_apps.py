"""Bring back apps whose workspace survived but whose record did not.

An app is two things: an Output record and a workspace folder. The record is what makes it appear;
the folder is what holds the work. Lose the record and the work is still on disk, completely
invisible, with no way for the user to know it is there.

Only workspaces that hold REAL work come back. A workspace whose meta.json says "Untitled App", or
has none at all, is a template seed that was created and never used; resurrecting those would hand
every user a pile of empty cards, which is a worse product than the bug.

This runs once ever, behind a marker. Deleting an app leaves its workspace behind, so a recovery
that ran on every boot would make deletion impossible: the app would return the next morning.
"""

import json
import logging
import os
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

from backend.apps.outputs.models import Output
from backend.config.paths import DATA_ROOT, OUTPUTS_WORKSPACE_DIR

logger = logging.getLogger(__name__)

P_MARKER = os.path.join(DATA_ROOT, "orphan_app_recovery.done")
# What the seeder writes before a user has named anything, so it means "never used", not "an app".
P_PLACEHOLDER_NAMES = {"untitled app", "untitled", ""}


class RecoveryReport(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    scanned: int = 0
    recovered: List[str] = []
    skipped_unused: int = 0


@typechecked
def p_real_name(workspace_dir: str) -> Optional[str]:
    """The app's own name, or None when this workspace was never actually used."""
    meta = os.path.join(workspace_dir, "meta.json")
    if not os.path.isfile(meta):
        return None
    try:
        with open(meta, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    name = data.get("name")
    if not isinstance(name, str) or name.strip().lower() in P_PLACEHOLDER_NAMES:
        return None
    return name.strip()


@typechecked
def p_description(workspace_dir: str) -> str:
    meta = os.path.join(workspace_dir, "meta.json")
    try:
        with open(meta, encoding="utf-8") as f:
            desc = json.load(f).get("description")
        return desc if isinstance(desc, str) else ""
    except (OSError, ValueError):
        return ""


@typechecked
def recover_orphaned_apps(force: bool = False) -> RecoveryReport:
    """Re-register orphaned workspaces that hold real work. Runs once unless forced."""
    report = RecoveryReport()
    # Cheap checks BEFORE the import: this runs on every boot and pays for itself exactly once.
    if not force and os.path.exists(P_MARKER):
        return report
    if not os.path.isdir(OUTPUTS_WORKSPACE_DIR):
        return report
    from backend.apps.outputs.workspace_io import load_all, save

    claimed = {o.workspace_id for o in load_all() if o.workspace_id}
    for entry in sorted(os.listdir(OUTPUTS_WORKSPACE_DIR)):
        path = os.path.join(OUTPUTS_WORKSPACE_DIR, entry)
        if not os.path.isdir(path) or entry in claimed:
            continue
        report.scanned += 1
        name = p_real_name(path)
        if name is None:
            report.skipped_unused += 1
            continue
        try:
            save(Output(name=name, description=p_description(path), workspace_id=entry))
        except Exception:
            logger.warning("could not re-register orphaned app workspace %s", entry, exc_info=True)
            continue
        report.recovered.append(name)

    if report.recovered:
        logger.info("recovered %d orphaned app(s): %s", len(report.recovered), ", ".join(report.recovered))
    try:
        os.makedirs(os.path.dirname(P_MARKER), exist_ok=True)
        with open(P_MARKER, "w", encoding="utf-8") as f:
            f.write(json.dumps({"recovered": report.recovered, "skipped_unused": report.skipped_unused}))
    except OSError:
        logger.warning("could not write the app-recovery marker; it may run again", exc_info=True)
    return report
