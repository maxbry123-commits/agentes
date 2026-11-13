"""Pure session-construction for resume + duplicate, lifted out of agent_manager.
These BUILD an AgentSession and return it; the caller owns the in-memory store write
and the UI notify (store-before-notify is load-bearing, a client must never be told
about a session it can't yet fetch)."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from typeguard import typechecked

from backend.apps.agents.core.models import AgentSession, Message, MessageBranch
from backend.apps.agents.manager.session.apply_context_window import apply_context_window
from backend.apps.agents.manager.session.session_store import load_session_data


@typechecked
def load_session_for_resume(session_id: str) -> AgentSession:
    """Build a live AgentSession from its on-disk JSON snapshot. The disk copy stays put
    (the history list reads from disk; deleting on resume would erase it). Raises if absent."""
    data = load_session_data(session_id)
    if data is None:
        raise ValueError(f"Session {session_id} not found in history")
    session = AgentSession(**data)
    apply_context_window(session)
    session.closed_at = None
    return session


@typechecked
def build_duplicate_session(
    source: Optional[AgentSession],
    session_id: str,
    dashboard_id: Optional[str],
    up_to_message_id: Optional[str],
) -> AgentSession:
    """Build an independent copy of a session with the same chat history but fresh ids
    (so branching the copy can't disturb the original). Raises if the source can't be found."""
    if not source:
        data = load_session_data(session_id)
        if data is None:
            raise ValueError(f"Session {session_id} not found")
        source = AgentSession(**data)
        apply_context_window(source)

    source_messages = list(source.messages)
    if up_to_message_id:
        cut_idx = next(
            (i for i, m in enumerate(source_messages) if m.id == up_to_message_id),
            None,
        )
        if cut_idx is not None:
            source_messages = source_messages[: cut_idx + 1]

    old_to_new_msg: Dict[str, str] = {}
    new_messages: List[Message] = []
    for msg in source_messages:
        new_id = uuid4().hex
        old_to_new_msg[msg.id] = new_id
        new_messages.append(Message(
            id=new_id,
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp,
            branch_id=msg.branch_id,
            parent_id=old_to_new_msg.get(msg.parent_id) if msg.parent_id else None,
            context_paths=msg.context_paths,
            attached_skills=msg.attached_skills,
            forced_tools=msg.forced_tools,
            images=msg.images,
        ))

    new_branches: Dict[str, MessageBranch] = {}
    for bid, branch in source.branches.items():
        new_branches[bid] = MessageBranch(
            id=bid,
            parent_branch_id=branch.parent_branch_id,
            fork_point_message_id=old_to_new_msg.get(branch.fork_point_message_id) if branch.fork_point_message_id else None,
            created_at=branch.created_at,
        )

    new_session = AgentSession(
        id=uuid4().hex,
        name=f"{source.name} (copy)",
        status="stopped",
        model=source.model,
        mode=source.mode,
        system_prompt=source.system_prompt,
        allowed_tools=list(source.allowed_tools),
        max_turns=source.max_turns,
        cwd=source.cwd,
        created_at=datetime.now(),
        messages=new_messages,
        branches=new_branches,
        active_branch_id=source.active_branch_id,
        tool_group_meta=dict(source.tool_group_meta),
        dashboard_id=dashboard_id or source.dashboard_id,
        sdk_session_id=source.sdk_session_id,
        needs_fork=True,
    )
    apply_context_window(new_session)
    return new_session
