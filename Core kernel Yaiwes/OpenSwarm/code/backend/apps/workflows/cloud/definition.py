"""The copy of a workflow the cloud is allowed to hold.

Two jobs. First, drop everything the runner cannot use: local session ids, run
history, dashboard placement, and the escalation tiers (which carry the user's
phone number and could not ring anyone from a container anyway). Second, be
stable, so hashing it detects a real edit and not the clock ticking.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

from typeguard import typechecked

from backend.apps.workflows.models import Workflow

# Anything that changes on its own, points at something only this machine has, or is nobody else's business.
LOCAL_ONLY_FIELDS = (
    "deleted_at",
    "draft_steps",
    "next_run_at",
    "last_run_at",
    "last_run_status",
    "last_run_id",
    "created_at",
    "updated_at",
    "source_session_id",
    "edit_agent_session_id",
    "schedule_agent_session_id",
    "last_test_session_id",
    "dashboard_id",
    "unsaved",
    "auto_named",
    "tested_signature",
    "step_tool_usage",
    "permissions",
    "cloud_workflow_id",
    "cloud_definition_signature",
)


@typechecked
def cloud_definition(wf: Workflow) -> Dict[str, Any]:
    body = wf.model_dump(mode="json")
    for field in LOCAL_ONLY_FIELDS:
        body.pop(field, None)
    # The cloud owns the timer for this copy; a live schedule inside it would be a second one.
    schedule = body.get("schedule")
    if isinstance(schedule, dict):
        schedule["enabled"] = False
    body["execution_target"] = "cloud"
    return body


@typechecked
def definition_signature(
    definition: Dict[str, Any], schedule: Dict[str, Any], context: Optional[Dict[str, Any]] = None
) -> str:
    """Fingerprint of exactly what we last handed the cloud, schedule and skills included,
    so "your edits are not up there yet" is a fact rather than a guess. Editing a skill a
    workflow leans on is an edit to that workflow's behaviour, so it belongs in here."""
    payload = json.dumps(
        {"definition": definition, "schedule": schedule, "context": context or {}}, sort_keys=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
