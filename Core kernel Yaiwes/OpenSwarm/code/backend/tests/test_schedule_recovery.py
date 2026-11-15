"""Recovery + missed-run edges the e2e suite leaves uncovered.

test_schedule_e2e already covers reconcile capture, the over-cap collapse, and
the friendly stuck-run message. This adds the boundaries it skips: the summary
heal on a stuck run, and the exactly-at-cap / empty cases of _capture_missed.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_schedule_recovery.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture(autouse=True)
def _wf_env(isolated_workflows_data, reset_scheduler_state):
    yield


def test_stuck_run_heals_workflow_summary(make_wf):
    """When the dead 'running' run is also the workflow's last run, the reaper
    must fix the summary too, not just the run row, or the detail header keeps
    showing a spinner forever."""
    from backend.apps.workflows import storage, scheduler
    from backend.apps.workflows.models import WorkflowRun
    wf = make_wf()
    run = WorkflowRun(workflow_id=wf.id, status="running")
    wf.last_run_id = run.id
    wf.last_run_status = "running"
    storage.save_workflow(wf)
    storage.record_run(run)

    scheduler._mark_stuck_runs_failed()

    healed = storage.get_workflow(wf.id)
    assert healed.last_run_status == "failure"


def test_capture_missed_exactly_at_cap_keeps_all_no_skipped(make_wf):
    from backend.apps.workflows import storage, scheduler
    wf = make_wf()
    storage.save_workflow(wf)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    missed = [base + timedelta(minutes=15 * i) for i in range(scheduler.PER_WORKFLOW_MISSED_CAP)]
    scheduler._capture_missed(wf, missed)
    assert len(storage.list_missed()) == scheduler.PER_WORKFLOW_MISSED_CAP
    assert [r for r in storage.list_runs(wf.id, limit=50) if r.status == "skipped"] == []


def test_capture_missed_empty_is_noop(make_wf):
    from backend.apps.workflows import storage, scheduler
    wf = make_wf()
    storage.save_workflow(wf)
    scheduler._capture_missed(wf, [])
    assert storage.list_missed() == []
    assert storage.list_runs(wf.id) == []
