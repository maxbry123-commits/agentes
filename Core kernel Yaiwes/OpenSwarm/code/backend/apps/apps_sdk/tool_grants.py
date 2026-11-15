"""Per-app grants for MCP tool calls made FROM apps: default is ask-the-user, decisions can be
remembered per app+tool, and the deny path is enforced HERE, server-side, so no app-side code
can widen its own surface. The grant decides IF a call may happen; mcp_call is HOW."""

import asyncio
import json
import os
import threading
import uuid
from typing import Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, InstanceOf
from typeguard import typechecked

from backend.apps.settings.store import DATA_DIR

GRANTS_FILE = os.path.join(DATA_DIR, "app_tool_grants.json")
GRANT_WAIT_SECONDS = 120.0

p_lock = threading.Lock()


class PendingGrant(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    request_id: str
    output_id: str
    tool_key: str
    event: InstanceOf[asyncio.Event]
    allow: bool = False
    remember: bool = False


p_pending: Dict[str, PendingGrant] = {}


@typechecked
def p_read_grants() -> Dict[str, Dict[str, str]]:
    try:
        with open(GRANTS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {str(k): {str(t): str(d) for t, d in v.items()} for k, v in raw.items()}
    except Exception:
        return {}


@typechecked
def p_write_grants(grants: Dict[str, Dict[str, str]]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = GRANTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(grants, f, indent=2)
    os.replace(tmp, GRANTS_FILE)


@typechecked
def grant_status(output_id: str, tool_key: str) -> Optional[str]:
    with p_lock:
        return p_read_grants().get(output_id, {}).get(tool_key)


@typechecked
def set_grant(output_id: str, tool_key: str, decision: Literal["granted", "denied"]) -> None:
    with p_lock:
        grants = p_read_grants()
        grants.setdefault(output_id, {})[tool_key] = decision
        p_write_grants(grants)


@typechecked
def clear_grants(output_id: str) -> None:
    """Reset an app to ask-by-default: forgets its remembered Always/Never decisions."""
    with p_lock:
        grants = p_read_grants()
        if grants.pop(output_id, None) is not None:
            p_write_grants(grants)


@typechecked
async def request_grant(output_id: str, app_name: str, tool_key: str, tool_label: str, args_preview: str) -> bool:
    """Ask the user over the websocket and block until they answer or the wait expires. Timeout and
    a closed dialog both read as deny: silence is never consent."""
    from backend.apps.agents.core.ws_manager import ws_manager

    pending = PendingGrant(request_id=uuid.uuid4().hex, output_id=output_id, tool_key=tool_key, event=asyncio.Event())
    p_pending[pending.request_id] = pending
    try:
        await ws_manager.broadcast_global("apps_sdk:tool_grant_request", {
            "request_id": pending.request_id,
            "output_id": output_id,
            "app_name": app_name,
            "tool_key": tool_key,
            "tool_label": tool_label,
            "args_preview": args_preview[:400],
        })
        try:
            await asyncio.wait_for(pending.event.wait(), timeout=GRANT_WAIT_SECONDS)
        except asyncio.TimeoutError:
            return False
        if pending.remember:
            set_grant(output_id, tool_key, "granted" if pending.allow else "denied")
        return pending.allow
    finally:
        p_pending.pop(pending.request_id, None)


@typechecked
def resolve_grant(request_id: str, allow: bool, remember: bool) -> bool:
    pending = p_pending.get(request_id)
    if pending is None:
        return False
    pending.allow = allow
    pending.remember = remember
    pending.event.set()
    return True
