"""Permission-policy resolution + the HITL approval flow, lifted out of the agent loop.
effective_policy/set_tool_policy resolve and persist a tool's policy through the SAME slot
(builtin vs custom tool), and request_user_approval surfaces the approval card and waits for
the user's decision (the wait itself lives in ws_manager.send_approval_request). builtin_perms
is the live in-memory snapshot the loop also reads, threaded in so an 'Always approve' takes
effect for the running agent, not only after a restart."""

import logging
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from typeguard import typechecked

from backend.apps.agents.core.models import AgentSession, ApprovalRequest
from backend.apps.agents.core.ws_manager import ws_manager
from backend.apps.agents.manager.permissions import path_gate
from backend.apps.agents.manager.permissions.ApprovalDecision import ApprovalDecision
from backend.apps.tools_lib.tools_lib import (
    load_all_tools as load_all_tools,
    save as save_tool,
    load_builtin_permissions,
    load_trusted_sensitive_paths,
    resolve_policy_slot,
    save_builtin_permissions,
    save_trusted_sensitive_paths,
)

logger = logging.getLogger(__name__)


@typechecked
def effective_policy(tool_name: str, builtin_perms: Dict[str, str], defaults: Dict[str, str]) -> str:
    """'always_allow', 'deny', or 'ask' for any tool, keyed through the shared slot resolver
    so the read slot matches the write slot exactly."""
    tools = load_all_tools()
    slot = resolve_policy_slot(tool_name, tools)
    if slot.store == "builtin":
        return builtin_perms.get(slot.key, defaults.get(slot.key, "always_allow"))
    if slot.key is not None:
        for t in tools:
            if t.id == slot.key:
                return t.tool_permissions.get(slot.action, "ask")
    return defaults.get(tool_name, "always_allow")


@typechecked
def set_tool_policy(tool_name: str, policy: str, builtin_perms: Dict[str, str]) -> None:
    """Persist `policy` into the SAME slot effective_policy reads AND update the live
    in-memory snapshot, so an 'Always approve' takes effect immediately."""
    tools = load_all_tools()
    slot = resolve_policy_slot(tool_name, tools)
    if slot.store == "builtin":
        builtin_perms[slot.key] = policy
        perms = load_builtin_permissions()
        perms[slot.key] = policy
        save_builtin_permissions(perms)
        return
    if slot.key is not None:
        for t in tools:
            if t.id == slot.key:
                t.tool_permissions[slot.action] = policy
                save_tool(t)
                return


@typechecked
async def request_user_approval(
    session: AgentSession,
    session_id: str,
    tool_name: str,
    tool_input: object,
    builtin_perms: Dict[str, str],
    sensitive_pattern: Optional[str] = None,
    timeout: float = 600.0,
) -> ApprovalDecision:
    """Send an approval request over WS and wait for the user's decision."""
    safe_input = tool_input if isinstance(tool_input, dict) else {}
    request_id = uuid4().hex
    label, why = (None, None)
    if sensitive_pattern:
        described = path_gate.describe_sensitive_pattern(sensitive_pattern)
        if described:
            label, why = described
    approval_req = ApprovalRequest(
        id=request_id,
        session_id=session_id,
        tool_name=tool_name,
        tool_input=safe_input,
        sensitive_pattern=sensitive_pattern,
        sensitive_label=label,
        sensitive_why=why,
    )
    session.pending_approvals.append(approval_req)
    session.status = "waiting_approval"
    await ws_manager.send_to_session(session_id, "agent:status", {
        "session_id": session_id,
        "status": "waiting_approval",
    })
    decision = ApprovalDecision.model_validate(await ws_manager.send_approval_request(
        session_id, request_id, tool_name, safe_input,
        timeout=timeout,
        sensitive_pattern=sensitive_pattern,
        sensitive_label=label,
        sensitive_why=why,
    ))
    # Persist a trusted sensitive-path so later prompts for the same pattern skip the modal.
    if (
        decision.behavior == "allow"
        and decision.trust_pattern
        and sensitive_pattern
    ):
        try:
            existing = load_trusted_sensitive_paths()
            if sensitive_pattern not in existing:
                existing.append(sensitive_pattern)
                save_trusted_sensitive_paths(existing)
        except Exception:
            logger.exception("Failed to persist trusted sensitive path")
    # "Always approve": persist the tool policy (the sensitive/catastrophic guards still re-fire).
    if decision.behavior == "allow" and decision.set_always_allow:
        try:
            set_tool_policy(tool_name, "always_allow", builtin_perms)
        except Exception:
            logger.exception("Failed to persist always-allow for %s", tool_name)
    approval_latency_ms = int((datetime.now() - approval_req.created_at).total_seconds() * 1000)
    try:
        session.approval_decisions.append({
            "tool": tool_name,
            "behavior": decision.behavior,
            "decision_ms": approval_latency_ms,
        })
    except Exception:
        pass
    session.pending_approvals = [a for a in session.pending_approvals if a.id != request_id]
    session.status = "running"
    await ws_manager.send_to_session(session_id, "agent:status", {
        "session_id": session_id,
        "status": "running",
    })
    return decision
