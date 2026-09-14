"""Referential integrity for workflows: no transcript outlives a hard delete, no pointer outlives
its session.

Two failures of the same class, both seen live:
  - Purge removed the workflow and its runs and left the chat transcripts on disk forever. The user
    asked for an irreversible delete and the conversation survived it.
  - 0 of 5 workflow chat pointers resolved in the real packaged store, so the UI read a pointer,
    got nothing, and rendered a blank panel instead of an empty state.

The last test here is the one that matters most: it pins OWNED_SESSION_FIELDS against the model, so
adding a fourth sticky session pointer and forgetting to clean it up fails CI instead of quietly
leaking a transcript six months from now.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_reference_integrity.py -v
"""

from __future__ import annotations

import pytest

from backend.apps.workflows import storage
from backend.apps.workflows.models import Workflow
from backend.apps.workflows.owned_sessions import (
    OWNED_SESSION_FIELDS,
    REFERENCED_SESSION_FIELDS,
    owned_session_ids,
    purge_owned_sessions,
    retire_previous_test_session,
)
from backend.apps.workflows.reconcile_references import reconcile_workflow_sessions


@pytest.fixture(autouse=True)
def p_wf_env(isolated_workflows_data, reset_scheduler_state, tmp_path, monkeypatch):
    # isolated_workflows_data isolates workflows but NOT sessions, so without this the fixture
    # transcripts below land in the developer's real backend/data/sessions and stay there.
    import backend.apps.agents.manager.session.session_store as store
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setattr(store, "sessions_dir", lambda: str(sessions))
    yield


def p_session_on_disk(sid: str) -> None:
    from backend.apps.agents.manager.session.session_store import save_session
    save_session(sid, {"id": sid, "name": "t", "messages": []})


def p_session_exists(sid: str) -> bool:
    from backend.apps.agents.manager.session.session_store import load_session_data
    return load_session_data(sid) is not None


def test_owned_ids_collects_every_owned_pointer(make_wf):
    wf = make_wf(
        edit_agent_session_id="s-edit",
        schedule_agent_session_id="s-sched",
        last_test_session_id="s-test",
    )
    assert sorted(owned_session_ids(wf)) == ["s-edit", "s-sched", "s-test"]


def test_the_originating_chat_is_never_owned(make_wf):
    """source_session_id is the user's own chat that the workflow was generated from. Deleting it
    on purge would destroy a real conversation nobody asked to lose."""
    wf = make_wf(source_session_id="s-users-own-chat")
    assert owned_session_ids(wf) == []


@pytest.mark.asyncio
async def test_purge_takes_the_transcripts_with_it(make_wf):
    wf = make_wf(edit_agent_session_id="s-edit", last_test_session_id="s-test")
    for sid in ("s-edit", "s-test"):
        p_session_on_disk(sid)
    assert p_session_exists("s-edit")

    removed = await purge_owned_sessions(wf)

    assert removed == 2
    assert not p_session_exists("s-edit"), "a hard delete must not leave the conversation behind"
    assert not p_session_exists("s-test")


@pytest.mark.asyncio
async def test_purge_spares_the_originating_chat(make_wf):
    wf = make_wf(edit_agent_session_id="s-edit", source_session_id="s-users-own-chat")
    p_session_on_disk("s-edit")
    p_session_on_disk("s-users-own-chat")

    await purge_owned_sessions(wf)

    assert not p_session_exists("s-edit")
    assert p_session_exists("s-users-own-chat"), "the user's own chat outlives the workflow"


@pytest.mark.asyncio
async def test_a_second_test_run_retires_the_first(make_wf):
    """Live: building one workflow ran five tests and left five orphan cards on the canvas. Each new
    test overwrites last_test_session_id, so the displaced chat had no pointer left and would have
    survived a hard delete of the workflow."""
    wf = make_wf(last_test_session_id="s-test-1")
    p_session_on_disk("s-test-1")

    await retire_previous_test_session(wf)

    assert wf.last_test_session_id is None
    assert not p_session_exists("s-test-1"), "the displaced test chat must not outlive its pointer"


@pytest.mark.asyncio
async def test_retiring_with_no_previous_test_is_a_no_op(make_wf):
    """The discriminating half: the first test of a workflow must not try to drop anything."""
    wf = make_wf(edit_agent_session_id="s-edit")
    p_session_on_disk("s-edit")

    await retire_previous_test_session(wf)

    assert p_session_exists("s-edit"), "retiring a test must never touch the edit chat"


def test_reconcile_nulls_a_pointer_whose_session_is_gone(make_wf):
    wf = make_wf(edit_agent_session_id="s-vanished")
    storage.save_workflow(wf)

    report = reconcile_workflow_sessions()

    assert report.pointers_cleared == 1
    assert report.workflows_scanned == 1
    assert storage.get_workflow(wf.id).edit_agent_session_id is None


def test_reconcile_leaves_a_live_pointer_alone(make_wf):
    """The discriminating half. A sweep that nulls everything would destroy working history."""
    p_session_on_disk("s-alive")
    wf = make_wf(edit_agent_session_id="s-alive")
    storage.save_workflow(wf)

    report = reconcile_workflow_sessions()

    assert report.pointers_cleared == 0
    assert storage.get_workflow(wf.id).edit_agent_session_id == "s-alive"


def test_reconcile_covers_trashed_workflows(make_wf):
    """Otherwise restoring from Trash hands back a pointer that already dangles."""
    from datetime import datetime
    wf = make_wf(edit_agent_session_id="s-vanished", deleted_at=datetime.now())
    storage.save_workflow(wf)

    reconcile_workflow_sessions()

    assert storage.get_workflow(wf.id).edit_agent_session_id is None


def test_reconcile_is_idempotent(make_wf):
    wf = make_wf(edit_agent_session_id="s-vanished")
    storage.save_workflow(wf)
    reconcile_workflow_sessions()
    assert reconcile_workflow_sessions().pointers_cleared == 0


def test_every_session_pointer_on_the_model_is_classified():
    """THE seal on this bug class. Any new *_session_id field on Workflow must be declared either
    owned (purged with the workflow) or referenced (spared). Forgetting leaks a transcript past a
    hard delete, and this fails loudly instead of letting that ship."""
    declared = set(OWNED_SESSION_FIELDS) | set(REFERENCED_SESSION_FIELDS)
    on_model = {f for f in Workflow.model_fields if f.endswith("_session_id")}
    missing = on_model - declared
    assert not missing, (
        f"{sorted(missing)} is a session pointer nobody classified. Add it to OWNED_SESSION_FIELDS "
        f"(deleted with the workflow) or REFERENCED_SESSION_FIELDS (survives it)."
    )
