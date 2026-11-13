"""Reading a finished session correctly, including the failures the backend calls success."""

import subprocess
import sys
import time
from typing import Any, Dict, Iterator

import httpx
import pytest

from runner import workflow_run
from runner.boot.backend_process import BackendProcess
from runner.workflow_run import (
    WorkflowRunFailed,
    execute_workflow,
    final_answer,
    render_transcript,
    system_notices,
    trigger_run,
)

# Shape taken verbatim from a real container run whose provider token was rejected.
REJECTED_TOKEN_SESSION = [
    {"role": "user", "content": "Reply with exactly the word PONG and nothing else."},
    {"role": "system", "content": "Provider authentication expired. Open Settings, Models and reconnect, then send your message again."},
]

ANSWERED_SESSION = [
    {"role": "user", "content": "ping"},
    {"role": "assistant", "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "echo hi"}}]},
    {"role": "assistant", "content": [{"type": "text", "text": "PONG"}]},
    {"role": "assistant", "content": [{"type": "text", "text": "draft"}], "hidden": True},
]


def test_a_rejected_credential_surfaces_as_a_system_notice() -> None:
    assert system_notices(REJECTED_TOKEN_SESSION) == [REJECTED_TOKEN_SESSION[1]["content"]]
    assert final_answer(REJECTED_TOKEN_SESSION) == ""


def test_a_healthy_run_raises_no_notices() -> None:
    assert system_notices(ANSWERED_SESSION) == []


def test_the_answer_is_the_last_visible_assistant_text() -> None:
    assert final_answer(ANSWERED_SESSION) == "PONG"


def test_the_transcript_keeps_tool_calls_and_drops_hidden_turns() -> None:
    transcript = render_transcript(ANSWERED_SESSION)
    assert "[tool Bash]" in transcript
    assert "PONG" in transcript
    assert "draft" not in transcript


# A backend busy enough to miss a reply is the normal case, not a broken one: a single MCP
# registry call has been measured holding its event loop past a minute. These pin that a late
# reply never costs the user the run.

RUN_ROW = {"id": "run_1", "status": "success", "session_id": "sess_1", "cost_usd": 0.0}


@pytest.fixture
def backend() -> Iterator[BackendProcess]:
    """A real BackendProcess around a process that just sits there, so is_alive() is honest."""
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        yield BackendProcess(process=process, base_url="http://backend.test", token="t")
    finally:
        process.kill()
        process.wait(timeout=10)


def p_client(stalls: int) -> httpx.Client:
    """A client whose first `stalls` requests time out, exactly like a starved event loop."""
    state = {"left": stalls}

    def handle(request: httpx.Request) -> httpx.Response:
        if state["left"] > 0:
            state["left"] -= 1
            raise httpx.ReadTimeout("timed out", request=request)
        if request.url.path.endswith("/run"):
            return httpx.Response(200, json={"run_id": "run_1", "status": "running"})
        if request.url.path.endswith("/runs"):
            return httpx.Response(200, json={"runs": [RUN_ROW]})
        return httpx.Response(404, json={})

    return httpx.Client(transport=httpx.MockTransport(handle), timeout=1.0)


def test_a_stalled_trigger_adopts_the_run_it_already_started(backend: BackendProcess) -> None:
    # One unanswered POST, then the run it started is visible. Posting again would either run the
    # workflow twice or come back "Previous run still active".
    assert trigger_run(p_client(stalls=1), backend, "wf_1", time.monotonic() + 5.0) == "run_1"


def test_a_dead_backend_fails_the_trigger_instead_of_waiting(backend: BackendProcess) -> None:
    backend.process.kill()
    backend.process.wait(timeout=10)
    with pytest.raises(WorkflowRunFailed, match="backend died"):
        trigger_run(p_client(stalls=99), backend, "wf_1", time.monotonic() + 5.0)


def test_a_stalled_poll_does_not_throw_away_a_run_that_finishes(
    backend: BackendProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    polls = {"left": 2}

    def p_find(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        if polls["left"] > 0:
            polls["left"] -= 1
            raise httpx.ReadTimeout("timed out")
        return RUN_ROW

    monkeypatch.setattr(workflow_run, "trigger_run", lambda *_a, **_k: "run_1")
    monkeypatch.setattr(workflow_run, "p_find_run", p_find)
    monkeypatch.setattr(workflow_run, "p_collect_session", lambda *_a, **_k: ANSWERED_SESSION)
    monkeypatch.setattr(workflow_run, "POLL_INTERVAL_SECONDS", 0.01)

    outcome = execute_workflow(backend, "wf_1", time.monotonic() + 10.0)
    assert outcome.status == "success"
    assert outcome.answer == "PONG"
    assert polls["left"] == 0
