"""A cloud-hosted workflow's timer belongs to the server, not to this machine.

The failure these guard against is a double run: if the laptop is awake when a
cloud-hosted slot comes due, both the laptop and the server fire it, and the
user gets two of everything. Ownership is expressed once, on
Workflow.execution_target, and every reader of the schedule must honour it.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_schedule_execution_target.py -v
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture(autouse=True)
def p_wf_env(isolated_workflows_data, reset_scheduler_state):
    yield


def test_default_target_is_this_device(make_wf):
    """Every existing workflow predates the field, so the default has to keep them local."""
    wf = make_wf()
    assert wf.execution_target == "device"


@pytest.mark.asyncio
async def test_tick_does_not_fire_a_cloud_workflow(make_wf, monkeypatch):
    from backend.apps.workflows import storage, scheduler
    fired: list[str] = []

    async def p_capture(wf, scheduled_for=None):
        fired.append(wf.id)

    monkeypatch.setattr(scheduler, "_fire", p_capture)
    overdue = datetime.now(timezone.utc) - timedelta(minutes=5)

    local = make_wf(execution_target="device", next_run_at=overdue)
    cloud = make_wf(execution_target="cloud", next_run_at=overdue)
    storage.save_workflow(local)
    storage.save_workflow(cloud)

    await scheduler._tick()
    # _tick hands each fire to create_task, so nothing has actually run until we yield the loop.
    await asyncio.sleep(0)

    assert local.id in fired, "a device workflow must still fire; the test is vacuous otherwise"
    assert cloud.id not in fired


@pytest.mark.asyncio
async def test_tick_does_not_roll_a_cloud_next_run_at(make_wf, monkeypatch):
    """Rolling the timer forward locally is its own bug even when nothing fires: the server owns
    that field, and a local write silently competes with it."""
    from backend.apps.workflows import storage, scheduler

    async def p_noop(wf, scheduled_for=None):
        return None

    monkeypatch.setattr(scheduler, "_fire", p_noop)
    overdue = datetime.now(timezone.utc) - timedelta(minutes=5)
    cloud = make_wf(execution_target="cloud", next_run_at=overdue)
    storage.save_workflow(cloud)

    await scheduler._tick()

    after = storage.get_workflow(cloud.id)
    assert after.next_run_at == cloud.next_run_at


def test_sleep_math_ignores_cloud_workflows(make_wf):
    """_tick and seconds_to_next_fire must agree. If only _tick skipped cloud workflows, an
    overdue one would stay overdue forever and pin the loop at its 1s floor, burning a core."""
    from backend.apps.workflows import storage, scheduler
    overdue = datetime.now(timezone.utc) - timedelta(minutes=5)
    storage.save_workflow(make_wf(execution_target="cloud", next_run_at=overdue))

    assert scheduler.seconds_to_next_fire() is None
    assert scheduler._seconds_until_next() == 60.0


def test_reconcile_leaves_cloud_workflows_untouched(make_wf):
    """A closed laptop did not "miss" a cloud run; the server ran it. Capturing it would offer the
    user a review card for work that already happened, and rewrite a server-owned field."""
    from backend.apps.workflows import storage, scheduler
    anchor = datetime.now(timezone.utc) - timedelta(days=3)
    # occurrences_between never enumerates fires from before the workflow existed, so it has to be old.
    born = datetime.now(timezone.utc) - timedelta(days=10)
    cloud = make_wf(execution_target="cloud", next_run_at=anchor, created_at=born)
    storage.save_workflow(cloud)

    scheduler.reconcile_on_startup()

    assert storage.list_missed() == []
    after = storage.get_workflow(cloud.id)
    assert after.next_run_at == cloud.next_run_at


def test_reconcile_still_captures_device_workflows(make_wf):
    """The discriminating half: the same walk must keep working for local workflows."""
    from backend.apps.workflows import storage, scheduler
    anchor = datetime.now(timezone.utc) - timedelta(days=3)
    born = datetime.now(timezone.utc) - timedelta(days=10)
    local = make_wf(execution_target="device", next_run_at=anchor, created_at=born)
    storage.save_workflow(local)

    scheduler.reconcile_on_startup()

    assert storage.list_missed() != []
