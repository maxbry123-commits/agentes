"""The two schedulers have to agree on when "9am Monday" is.

A workflow can sit on this machine or on our servers, and the user is told a "next run" either way.
Two recurrence engines in two languages means two chances to be wrong, and the place they would
diverge is exactly the place wall-clock scheduling is hard: the morning a clock jumps forward and
2:30am never happens, and the morning it falls back and 1:30am happens twice.

The vector table below is duplicated verbatim in the cloud service's tests/workflow-schedule.test.ts.
Each row asserts the same answer on both sides, so if either engine drifts one of the suites fails.
Nothing here talks to the network; both halves are pure functions of a schedule and a moment.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from backend.apps.workflows.cloud.schedule import (
    CloudDailySchedule,
    CloudWeeklySchedule,
    ScheduleSupported,
    to_cloud_schedule,
    wire,
)
from backend.apps.workflows.models import ScheduleConfig, Workflow
from backend.apps.workflows.scheduler import compute_next_fire

LA = "America/Los_Angeles"

# (label, ScheduleConfig kwargs, asked at, fires at). Times are UTC because that is what both
# engines return; the point of each row is the LOCAL clock it corresponds to, named in the label.
VECTORS = [
    ("LA daily 9am, the Saturday before the clocks go forward",
     dict(repeat_unit="day", repeat_every=1, hour=9, minute=0, timezone=LA),
     "2026-03-06T20:00:00Z", "2026-03-07T17:00:00Z"),
    ("LA daily 9am, the day the clocks go forward",
     dict(repeat_unit="day", repeat_every=1, hour=9, minute=0, timezone=LA),
     "2026-03-07T20:00:00Z", "2026-03-08T16:00:00Z"),
    ("LA daily 9am, the day the clocks go back",
     dict(repeat_unit="day", repeat_every=1, hour=9, minute=0, timezone=LA),
     "2026-10-31T20:00:00Z", "2026-11-01T17:00:00Z"),
    ("LA weekdays 9am, asked Friday after the slot, over a spring-forward weekend",
     dict(repeat_unit="week", repeat_every=1, on_days=[1, 2, 3, 4, 5], hour=9, minute=0, timezone=LA),
     "2026-03-06T18:00:00Z", "2026-03-09T16:00:00Z"),
    ("LA weekdays 9am, asked Friday after the slot, over a fall-back weekend",
     dict(repeat_unit="week", repeat_every=1, on_days=[1, 2, 3, 4, 5], hour=9, minute=0, timezone=LA),
     "2026-10-30T18:00:00Z", "2026-11-02T17:00:00Z"),
    ("LA weekends 9am, asked on a Wednesday",
     dict(repeat_unit="week", repeat_every=1, on_days=[0, 6], hour=9, minute=0, timezone=LA),
     "2026-06-10T18:00:00Z", "2026-06-13T16:00:00Z"),
    ("LA daily 2:30am, an hour the clocks skip",
     dict(repeat_unit="day", repeat_every=1, hour=2, minute=30, timezone=LA),
     "2026-03-08T09:59:00Z", "2026-03-08T10:30:00Z"),
    ("LA daily 1:30am, first time through the repeated hour",
     dict(repeat_unit="day", repeat_every=1, hour=1, minute=30, timezone=LA),
     "2026-11-01T08:00:00Z", "2026-11-01T08:30:00Z"),
    ("LA daily 1:30am, asked at 1:45 the first time round, so today's slot has gone",
     dict(repeat_unit="day", repeat_every=1, hour=1, minute=30, timezone=LA),
     "2026-11-01T08:45:00Z", "2026-11-02T09:30:00Z"),
    ("LA daily 1:30am, asked at 1:15 the second time round, so it fires again this hour",
     dict(repeat_unit="day", repeat_every=1, hour=1, minute=30, timezone=LA),
     "2026-11-01T09:15:00Z", "2026-11-01T09:30:00Z"),
    ("LA daily 1:30am, asked at exactly 1:30, so this one has just gone",
     dict(repeat_unit="day", repeat_every=1, hour=1, minute=30, timezone=LA),
     "2026-11-01T08:30:00Z", "2026-11-02T09:30:00Z"),
    ("Berlin daily 2:30am, an hour the clocks skip",
     dict(repeat_unit="day", repeat_every=1, hour=2, minute=30, timezone="Europe/Berlin"),
     "2026-03-29T00:30:00Z", "2026-03-29T01:30:00Z"),
    ("Berlin daily 2:30am, the second time through the repeated hour",
     dict(repeat_unit="day", repeat_every=1, hour=2, minute=30, timezone="Europe/Berlin"),
     "2026-10-25T01:17:33Z", "2026-10-25T01:30:00Z"),
    ("Sydney Sundays 11:45pm, over their spring-forward",
     dict(repeat_unit="week", repeat_every=1, on_days=[0], hour=23, minute=45, timezone="Australia/Sydney"),
     "2026-10-02T05:00:00Z", "2026-10-04T12:45:00Z"),
    ("Kolkata daily 9am, a half-hour offset with no DST",
     dict(repeat_unit="day", repeat_every=1, hour=9, minute=0, timezone="Asia/Kolkata"),
     "2026-06-15T12:00:00Z", "2026-06-16T03:30:00Z"),
    ("UTC daily midnight, asked one second after it fired",
     dict(repeat_unit="day", repeat_every=1, hour=0, minute=0, timezone="UTC"),
     "2026-06-15T00:00:01Z", "2026-06-16T00:00:00Z"),
]


def p_moment(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def p_workflow(config: dict) -> Workflow:
    # created_at is the phase anchor for multi-period cadences. Every schedule here repeats once per
    # period, so it cannot move an answer; it is pinned only so nothing about these rows floats.
    return Workflow(
        title="agreement",
        created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        schedule=ScheduleConfig(enabled=True, **config),
    )


def test_the_local_scheduler_hits_every_vector():
    for label, config, asked, fires in VECTORS:
        assert compute_next_fire(p_workflow(config), p_moment(asked)) == p_moment(fires), label


def test_every_vector_maps_onto_a_schedule_the_cloud_can_hold():
    """A vector the cloud would refuse proves nothing about the two engines agreeing."""
    for label, config, *_ in VECTORS:
        mapping = to_cloud_schedule(ScheduleConfig(enabled=True, **config))
        assert isinstance(mapping, ScheduleSupported), label
        assert isinstance(mapping.schedule, (CloudDailySchedule, CloudWeeklySchedule)), label
        # The zone has to survive the trip, or the cloud does its maths in the wrong one.
        assert wire(mapping.schedule)["timezone"] == config["timezone"], label


def test_a_daily_nine_am_never_drifts_off_nine_am():
    """The reason the zone travels with the schedule at all: stored as a UTC hour, every one of
    these fires would move by an hour twice a year for anyone outside UTC."""
    wf = p_workflow(dict(repeat_unit="day", repeat_every=1, hour=9, minute=0, timezone=LA))
    cursor = datetime(2026, 3, 5, tzinfo=timezone.utc)
    days = set()
    for _ in range(250):
        cursor = compute_next_fire(wf, cursor)
        local = cursor.astimezone(ZoneInfo(LA))
        assert (local.hour, local.minute) == (9, 0), cursor.isoformat()
        days.add(local.date())
    assert len(days) == 250, "one fire per calendar day, none doubled and none skipped"
