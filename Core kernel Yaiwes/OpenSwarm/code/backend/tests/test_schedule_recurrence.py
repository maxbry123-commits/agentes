"""Pure recurrence + validator units not already covered by the semantics
suite (which owns the DST, monthly, daily/weekly-interval, and occurrence
timezone/end-condition cases). These functions take explicit reference
datetimes and touch no disk, so they need no scaffolding.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_schedule_recurrence.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


def _sched(**overrides):
    from backend.apps.workflows.models import ScheduleConfig
    base = dict(enabled=True, repeat_unit="day", repeat_every=1, hour=9, minute=0, timezone="UTC")
    base.update(overrides)
    return ScheduleConfig(**base)


# --- minute / hour intervals (day/week/month intervals live in semantics) ----

def test_minute_interval_steps_by_repeat_every_anchored():
    from backend.apps.workflows.scheduler import _next_fire_after
    sched = _sched(repeat_unit="minute", repeat_every=30)
    anchor = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    # Asking from 00:10 on the same grid -> next 30-min point is 00:30.
    ref = datetime(2026, 6, 1, 0, 10, tzinfo=timezone.utc)
    assert _next_fire_after(sched, ref, anchor) == datetime(2026, 6, 1, 0, 30, tzinfo=timezone.utc)


def test_minute_repeat_every_floored_at_15():
    """A sub-15 interval would be a token-burning loop; the floor lifts it to
    15 (enforced both by the validator and the scheduler's own max(15, ...))."""
    from backend.apps.workflows.scheduler import _next_fire_after
    sched = _sched(repeat_unit="minute", repeat_every=5)
    anchor = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    ref = datetime(2026, 6, 1, 0, 1, tzinfo=timezone.utc)
    assert _next_fire_after(sched, ref, anchor) == datetime(2026, 6, 1, 0, 15, tzinfo=timezone.utc)


def test_hourly_interval_fires_at_configured_minute():
    from backend.apps.workflows.scheduler import _next_fire_after
    sched = _sched(repeat_unit="hour", repeat_every=3, minute=20)
    anchor = datetime(2026, 6, 1, 0, 20, tzinfo=timezone.utc)
    ref = datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc)
    assert _next_fire_after(sched, ref, anchor) == datetime(2026, 6, 1, 3, 20, tzinfo=timezone.utc)


# --- p_first_after grid math -------------------------------------------------

def test_p_first_after_before_anchor_returns_anchor():
    from backend.apps.workflows.scheduler import p_first_after
    anchor = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    ref = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
    assert p_first_after(anchor, ref, timedelta(hours=1)) == anchor


def test_p_first_after_is_strict_on_exact_grid_point():
    from backend.apps.workflows.scheduler import p_first_after
    anchor = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    ref = datetime(2026, 6, 1, 2, 0, tzinfo=timezone.utc)  # exactly on the grid
    # strictly-after means we advance to the next point, not return ref.
    assert p_first_after(anchor, ref, timedelta(hours=1)) == datetime(2026, 6, 1, 3, 0, tzinfo=timezone.utc)


# --- fires_in_window (backs the cost estimate) -------------------------------

def test_fires_in_window_zero_when_disabled():
    from backend.apps.workflows import scheduler
    from backend.apps.workflows.models import Workflow, WorkflowStep
    wf = Workflow(title="t", steps=[WorkflowStep(text="hi")], schedule=_sched(enabled=False))
    assert scheduler.fires_in_window(wf, days=30) == 0


def test_fires_in_window_capped_by_remaining_max_runs():
    """With 2 runs left on a daily schedule, a 30-day window projects exactly 2
    fires, not 30."""
    from backend.apps.workflows import scheduler
    from backend.apps.workflows.models import Workflow, WorkflowStep
    wf = Workflow(title="t", steps=[WorkflowStep(text="hi")],
                  schedule=_sched(max_runs=10, runs_count=8))
    assert scheduler.fires_in_window(wf, days=30) == 2


# --- occurrences_between cap -------------------------------------------------

def test_occurrences_between_respects_cap():
    from backend.apps.workflows import scheduler
    from backend.apps.workflows.models import Workflow, WorkflowStep
    wf = Workflow(title="t", steps=[WorkflowStep(text="hi")], schedule=_sched(repeat_unit="day"))
    wf.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    fires = scheduler.occurrences_between(
        wf,
        datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 30, 0, 0, tzinfo=timezone.utc),
        cap=5,
    )
    assert len(fires) == 5


# --- ScheduleConfig validators -----------------------------------------------

def test_clean_on_days_drops_out_of_range_and_dedupes_preserving_order():
    from backend.apps.workflows.models import ScheduleConfig
    sched = ScheduleConfig(repeat_unit="week", on_days=[3, 7, -1, 3, 0, 6])
    assert sched.on_days == [3, 0, 6]


def test_interval_bounds_clamp_minute_unit_to_15_1440():
    from backend.apps.workflows.models import ScheduleConfig
    assert ScheduleConfig(repeat_unit="minute", repeat_every=5).repeat_every == 15
    assert ScheduleConfig(repeat_unit="minute", repeat_every=99999).repeat_every == 1440


def test_interval_bounds_clamp_other_units_to_365():
    from backend.apps.workflows.models import ScheduleConfig
    assert ScheduleConfig(repeat_unit="day", repeat_every=99999).repeat_every == 365
