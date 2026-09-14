"""HTTP surface for app version history. Thin: each route validates then
delegates to versions.py. Its own SubApp so the already-large outputs.py doesn't
grow, and so the agent-running restore guard lives next to the route, not in the
pure store. Prefix: /api/output_versions."""
import logging
import os
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from backend.apps.outputs import versions
from backend.apps.outputs.workspace_io import load_output
from backend.config.Apps import SubApp
from backend.config.paths import OUTPUTS_VERSIONS_DIR

logger = logging.getLogger(__name__)


@asynccontextmanager
async def output_versions_lifespan():
    os.makedirs(OUTPUTS_VERSIONS_DIR, exist_ok=True)
    yield


output_versions = SubApp("output_versions", output_versions_lifespan)


class CaptureRequest(BaseModel):
    # Clients can only ask for auto/manual; pre_restore is set internally by restore.
    source: Literal["auto", "manual"] = "manual"
    label: str = ""
    thumbnail: Optional[str] = None


@output_versions.router.get("/{output_id}")
async def list_output_versions(output_id: str):
    return {"versions": [v.model_dump() for v in versions.list_versions(output_id)]}


@output_versions.router.post("/{output_id}")
async def capture_output_version(output_id: str, body: CaptureRequest):
    v = versions.capture(
        output_id, source=body.source, label=body.label, thumbnail=body.thumbnail
    )
    if v is None:
        raise HTTPException(status_code=404, detail="Output not found")
    return {"ok": True, "version": v.model_dump()}


@output_versions.router.post("/{output_id}/{version_id}/restore")
async def restore_output_version(output_id: str, version_id: str):
    output = load_output(output_id)
    if output is None:
        raise HTTPException(status_code=404, detail="Output not found")
    # Don't restore out from under a live builder run. The frontend disables the button while the agent is active; this is the backend half of that guard.
    if output.session_id:
        from backend.apps.agents.agent_manager import agent_manager
        session = agent_manager.sessions.get(output.session_id)
        if session and getattr(session, "status", None) in ("running", "waiting_approval"):
            raise HTTPException(
                status_code=409,
                detail="This app is still being edited. Wait for the current change to finish, then try again.",
            )
    restored = versions.restore(output_id, version_id)
    if restored is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"ok": True, "output": restored.model_dump()}


@output_versions.router.post("/{output_id}/{version_id}/branch")
async def branch_output_version(output_id: str, version_id: str):
    if load_output(output_id) is None:
        raise HTTPException(status_code=404, detail="Output not found")
    new_id = versions.branch(output_id, version_id)
    if new_id is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"ok": True, "new_output_id": new_id}
