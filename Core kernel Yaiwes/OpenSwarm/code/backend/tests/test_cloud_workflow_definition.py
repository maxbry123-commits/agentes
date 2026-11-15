"""What we are willing to hand the cloud, and which schedules it can honour at all.

Both are pure functions, and both decide something a user reads: a schedule the cloud cannot
express has to be refused in words rather than rounded off, and the copy we push must not carry
anything local (session ids, a phone number) off this machine.
"""
from datetime import datetime, timezone

from backend.apps.workflows.cloud import schedule as cloud_schedule
from backend.apps.workflows.cloud.definition import cloud_definition, definition_signature
from backend.apps.workflows.cloud.schedule import (
    ScheduleSupported,
    ScheduleUnsupported,
    to_cloud_schedule,
    wire,
)
from backend.apps.workflows.models import PermissionTier, ScheduleConfig, Workflow, WorkflowStep


def p_sched(**overrides) -> ScheduleConfig:
    base = dict(enabled=True, repeat_unit="day", repeat_every=1, hour=9, minute=0, timezone="UTC")
    base.update(overrides)
    return ScheduleConfig(**base)


def p_wf(**overrides) -> Workflow:
    base = dict(title="Morning digest", steps=[WorkflowStep(text="summarize the news")], schedule=p_sched())
    base.update(overrides)
    return Workflow(**base)


def test_interval_daily_and_weekday_schedules_map_to_the_cloud():
    for supported in (
        p_sched(),
        p_sched(repeat_unit="minute", repeat_every=30),
        p_sched(repeat_unit="hour", repeat_every=6),
        p_sched(repeat_unit="week", on_days=[1, 2, 3, 4, 5]),
        p_sched(max_runs=5),
        p_sched(ends_at=datetime(2027, 1, 1, tzinfo=timezone.utc)),
    ):
        assert isinstance(to_cloud_schedule(supported), ScheduleSupported)


def test_a_cadence_with_a_phase_the_wire_cannot_carry_is_refused_in_words():
    for unsupported in (
        p_sched(repeat_unit="month", day_of_month=1),
        p_sched(repeat_unit="day", repeat_every=3),
        p_sched(repeat_unit="week", repeat_every=2, on_days=[1]),
        # A weekly schedule with no days chosen is not a cadence yet, and saying "monthly" here would be a lie.
        p_sched(repeat_unit="week", on_days=[]),
    ):
        mapping = to_cloud_schedule(unsupported)
        assert isinstance(mapping, ScheduleUnsupported)
        # The reason is shown to a person verbatim, so it has to read like one wrote it.
        assert mapping.reason.endswith(".") and " " in mapping.reason


def test_a_wall_clock_time_travels_with_its_zone_and_not_as_a_utc_hour():
    """Storing 9am Tokyo as its UTC hour is how a schedule silently moves an hour twice a year."""
    mapping = to_cloud_schedule(p_sched(hour=9, minute=30, timezone="Asia/Tokyo"))
    assert isinstance(mapping, ScheduleSupported)
    assert wire(mapping.schedule) == {
        "kind": "daily", "hour": 9, "minute": 30, "timezone": "Asia/Tokyo",
    }


def test_weekdays_travel_sorted_and_end_conditions_ride_along():
    mapping = to_cloud_schedule(
        p_sched(
            repeat_unit="week",
            on_days=[5, 1, 3],
            max_runs=4,
            ends_at=datetime(2027, 3, 1, 12, 0, tzinfo=timezone.utc),
        )
    )
    assert isinstance(mapping, ScheduleSupported)
    assert wire(mapping.schedule) == {
        "kind": "weekly", "days": [1, 3, 5], "hour": 9, "minute": 0, "timezone": "UTC",
        "max_runs": 4, "ends_at": 1803902400000,  # 2027-03-01T12:00Z
    }


def test_a_legacy_local_zone_becomes_this_machines_real_zone(monkeypatch):
    """Records written before schedules carried a zone say "local". Sending that word, or flattening
    it to UTC, moves every one of their fires by this machine's whole offset."""
    monkeypatch.setattr(cloud_schedule, "host_timezone_name", lambda: "America/New_York")
    for stored in ("local", "", "Mars/Olympus_Mons"):
        mapping = to_cloud_schedule(p_sched(timezone=stored))
        assert isinstance(mapping, ScheduleSupported)
        assert wire(mapping.schedule)["timezone"] == "America/New_York", stored


def test_unset_end_conditions_are_absent_rather_than_null():
    """The cloud's schema takes an absent field, not a null one, so a null would 400 every push."""
    mapping = to_cloud_schedule(p_sched())
    assert isinstance(mapping, ScheduleSupported)
    assert "ends_at" not in wire(mapping.schedule)
    assert "max_runs" not in wire(mapping.schedule)


def test_the_cloud_copy_carries_no_local_secrets_and_no_live_timer():
    wf = p_wf(
        permissions=[PermissionTier(kind="text", after_minutes=5, phone="+15550001111")],
        edit_agent_session_id="session-abc",
        source_session_id="session-def",
    )
    body = cloud_definition(wf)
    assert "permissions" not in body, "the escalation tiers carry a phone number and cannot ring from a container"
    for leaked in ("edit_agent_session_id", "source_session_id", "last_run_id", "dashboard_id"):
        assert leaked not in body
    assert body["schedule"]["enabled"] is False
    assert body["steps"][0]["text"] == "summarize the news"


def test_a_signature_tracks_edits_and_ignores_the_clock():
    wf = p_wf()
    schedule = {"kind": "daily", "hour": 9, "minute": 0, "timezone": "UTC"}
    first = definition_signature(cloud_definition(wf), schedule)

    wf.title = wf.title
    assert definition_signature(cloud_definition(wf), schedule) == first, "a save with no edit is not a drift"

    wf.steps = [WorkflowStep(id=wf.steps[0].id, text="summarize the sports news")]
    assert definition_signature(cloud_definition(wf), schedule) != first
    assert definition_signature(cloud_definition(wf), {"kind": "interval", "minutes": 60}) != first
