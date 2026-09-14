"""Drive one workflow through the backend's own HTTP surface and collect its result.

Deliberately no shortcuts into agent_manager: the cloud run fires the same route the
Run button fires, so the MCP gate, action filtering, provider routing and history all
behave exactly as they do on a laptop.
"""

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field
from typeguard import typechecked

from runner.boot.backend_process import BackendProcess

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = ("success", "failure", "ran_late", "skipped")
POLL_INTERVAL_SECONDS = 1.0
TRANSCRIPT_MAX_CHARS = 14000
# The backend is one process on one event loop, and a heavy tool call can hold it: MCP registry
# work has been measured keeping it from answering for well over a minute. A reply that is late
# therefore means busy, not dead, so the budget is generous and lateness is never fatal. The only
# thing that ends a run early is the process actually exiting.
REQUEST_TIMEOUT_SECONDS = 60.0
TRIGGER_RETRY_SECONDS = 5.0


class WorkflowRunFailed(RuntimeError):
    """The backend refused to start the run at all."""


class RunProgress(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    run_id: str
    status: str
    active_step_idx: Optional[int] = None
    last_tool_label: Optional[str] = None


class RunOutcome(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    run_id: str
    status: str
    error: Optional[str] = None
    cost_usd: float = 0.0
    session_id: Optional[str] = None
    transcript: str = ""
    answer: str = ""
    system_notices: List[str] = Field(default_factory=list)


@typechecked
def p_block_text(block: Dict[str, Any]) -> str:
    kind = block.get("type")
    if kind == "text":
        return str(block.get("text") or "")
    if kind == "tool_use":
        return f"[tool {block.get('name')}] {json.dumps(block.get('input') or {})[:300]}"
    if kind == "tool_result":
        inner = block.get("content")
        return f"[result] {inner if isinstance(inner, str) else json.dumps(inner)[:300]}"
    return ""


@typechecked
def p_message_text(message: Dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [p_block_text(block) for block in content if isinstance(block, dict)]
        return "\n".join(part for part in parts if part)
    return ""


@typechecked
def render_transcript(messages: List[Dict[str, Any]]) -> str:
    """Role-tagged flatten, tail-biased so the end of a long run always survives the cap."""
    lines: List[str] = []
    for message in messages:
        if message.get("hidden"):
            continue
        text = p_message_text(message).strip()
        if text:
            lines.append(f"{str(message.get('role') or '?').upper()}: {text}")
    joined = "\n\n".join(lines)
    if len(joined) > TRANSCRIPT_MAX_CHARS:
        return "...(earlier turns trimmed)...\n\n" + joined[-TRANSCRIPT_MAX_CHARS:]
    return joined


@typechecked
def final_answer(messages: List[Dict[str, Any]]) -> str:
    """Last visible assistant text: the thing a user actually asked the workflow for."""
    for message in reversed(messages):
        if message.get("hidden") or message.get("role") != "assistant":
            continue
        text = p_message_text(message).strip()
        if text:
            return text
    return ""


@typechecked
def system_notices(messages: List[Dict[str, Any]]) -> List[str]:
    """Every system-role bubble in the session.

    The backend appends a system message only when something went wrong (a dead
    provider token, a run error, a blocked tool), and it does NOT fail the run for
    those, so a workflow whose credential was rejected still comes back "success".
    Keyed on the typed role, not on the prose, and reported rather than judged: the
    control plane decides what a notice means for billing and retries.
    """
    notices: List[str] = []
    for message in messages:
        if message.get("role") != "system" or message.get("hidden"):
            continue
        text = p_message_text(message).strip()
        if text:
            notices.append(text)
    return notices


@typechecked
def p_get_json(client: httpx.Client, backend: BackendProcess, path: str) -> Dict[str, Any]:
    response = client.get(f"{backend.base_url}{path}", headers=backend.headers())
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


@typechecked
def p_started_run_id(client: httpx.Client, backend: BackendProcess, workflow_id: str) -> Optional[str]:
    """The newest run on record, or None. Safe to adopt: the runs file ships empty in every
    container, so anything in this list was started by the POST we just made."""
    try:
        body = p_get_json(client, backend, f"/api/workflows/{workflow_id}/runs?limit=1")
    except httpx.HTTPError:
        return None
    for record in body.get("runs") or []:
        if isinstance(record, dict) and record.get("id"):
            return str(record["id"])
    return None


@typechecked
def trigger_run(client: httpx.Client, backend: BackendProcess, workflow_id: str, deadline: float) -> str:
    """Start the run, waiting out a backend too busy to answer instead of failing the job.

    A POST whose reply never arrived may still have started the run, so a retry looks for that
    run before firing again. Posting blind would either execute the workflow twice or come back
    "Previous run still active", and both are worse than waiting.
    """
    while True:
        try:
            response = client.post(
                f"{backend.base_url}/api/workflows/{workflow_id}/run",
                headers=backend.headers(),
                json={},
            )
            response.raise_for_status()
            body = response.json()
            break
        except httpx.HTTPError as exc:
            if not backend.is_alive():
                raise WorkflowRunFailed(f"backend died before the run could start: {exc}") from exc
            adopted = p_started_run_id(client, backend, workflow_id)
            if adopted:
                logger.warning("trigger reply never arrived (%s); adopting the run it started", exc)
                return adopted
            if time.monotonic() >= deadline:
                raise WorkflowRunFailed(f"backend never accepted the run trigger: {exc}") from exc
            logger.warning("trigger did not answer (%s); backend is busy, retrying", exc)
            time.sleep(TRIGGER_RETRY_SECONDS)

    run_id = str(body.get("run_id") or "")
    if not run_id:
        raise WorkflowRunFailed(
            f"backend accepted the trigger but never created a run for workflow {workflow_id}"
        )
    if body.get("status") == "failure":
        raise WorkflowRunFailed(str(body.get("error") or "run failed immediately"))
    return run_id


@typechecked
def p_find_run(client: httpx.Client, backend: BackendProcess, workflow_id: str, run_id: str) -> Dict[str, Any]:
    body = p_get_json(client, backend, f"/api/workflows/{workflow_id}/runs?limit=50")
    for record in body.get("runs") or []:
        if isinstance(record, dict) and record.get("id") == run_id:
            return record
    return {}


@typechecked
def p_stop_run(client: httpx.Client, backend: BackendProcess, run_id: str) -> None:
    try:
        client.post(f"{backend.base_url}/api/workflows/runs/{run_id}/stop", headers=backend.headers())
    except httpx.HTTPError:
        pass


@typechecked
def p_collect_session(client: httpx.Client, backend: BackendProcess, session_id: str) -> List[Dict[str, Any]]:
    try:
        body = p_get_json(client, backend, f"/api/agents/sessions/{session_id}")
    except httpx.HTTPError:
        return []
    messages = body.get("messages")
    return [m for m in messages if isinstance(m, dict)] if isinstance(messages, list) else []


@typechecked
def execute_workflow(
    backend: BackendProcess,
    workflow_id: str,
    deadline: float,
    on_progress: Optional[Callable[[RunProgress], None]] = None,
) -> RunOutcome:
    """Fire the workflow, poll it to a terminal state, and pull the transcript back.

    Blowing the deadline stops the run and reports `timed_out`; the caller still gets
    whatever the agent produced before the wall came down.
    """
    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        run_id = trigger_run(client, backend, workflow_id, deadline)
        record: Dict[str, Any] = {}
        timed_out = False

        while True:
            try:
                record = p_find_run(client, backend, workflow_id, run_id) or record
            except httpx.HTTPError as exc:
                # A poll that goes unanswered says the backend is busy, and the run it is busy
                # with is this one. Crashing here used to throw away a run that then finished fine.
                logger.warning("poll for run %s went unanswered (%s); still waiting", run_id, exc)
            status = str(record.get("status") or "running")
            if on_progress is not None:
                on_progress(RunProgress(
                    run_id=run_id,
                    status=status,
                    active_step_idx=record.get("active_step_idx"),
                    last_tool_label=record.get("last_tool_label"),
                ))
            if status in TERMINAL_STATUSES:
                break
            if not backend.is_alive():
                raise WorkflowRunFailed("backend died while the workflow was running")
            if time.monotonic() >= deadline:
                timed_out = True
                p_stop_run(client, backend, run_id)
                record = p_find_run(client, backend, workflow_id, run_id) or record
                break
            time.sleep(POLL_INTERVAL_SECONDS)

        session_id = record.get("session_id")
        messages = p_collect_session(client, backend, str(session_id)) if session_id else []
        return RunOutcome(
            run_id=run_id,
            status="timed_out" if timed_out else str(record.get("status") or "failure"),
            error=("wall-clock cap reached before the workflow finished" if timed_out else record.get("error")),
            cost_usd=float(record.get("cost_usd") or 0.0),
            session_id=str(session_id) if session_id else None,
            transcript=render_transcript(messages),
            answer=final_answer(messages),
            system_notices=system_notices(messages),
        )
