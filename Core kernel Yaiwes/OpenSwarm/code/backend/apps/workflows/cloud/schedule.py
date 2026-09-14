"""Map a local schedule onto the cloud scheduler's smaller vocabulary.

The cloud speaks three cadences: repeat every N minutes, once a day, or on the
weekdays you picked. Each can carry an end date and a run cap. What it does not
speak is a cadence with a phase longer than one period (every third day, every
other week, monthly), because the phase is anchored to the workflow's creation
on this machine and there is nowhere on the wire to put that anchor. Silently
rounding one of those off would fire a workflow on days the user never picked,
so it is refused here in the user's own words and stays on their machine.

The wall-clock kinds carry the IANA zone rather than a UTC hour. A UTC hour is a
schedule that moves by an hour twice a year for everyone outside UTC: "9am" set
in July quietly becomes 8am in November. The cloud does its recurrence maths in
the zone for the same reason scheduler._next_fire_after does.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

from backend.apps.workflows.models import ScheduleConfig
from backend.apps.workflows.scheduler import host_timezone_name

CADENCE_PREFIX = "Cloud runs repeat on an interval, once a day, or on the weekdays you pick."


class CloudScheduleBase(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    # Both optional, both meaning "and then it is finished". Sent only when set: the cloud's schema
    # takes an absent field, not a null one.
    ends_at: Optional[int] = None
    max_runs: Optional[int] = None


class CloudIntervalSchedule(CloudScheduleBase):
    kind: Literal["interval"] = "interval"
    minutes: int


class CloudDailySchedule(CloudScheduleBase):
    kind: Literal["daily"] = "daily"
    hour: int
    minute: int
    timezone: str


class CloudWeeklySchedule(CloudScheduleBase):
    kind: Literal["weekly"] = "weekly"
    # Sunday=0, the same convention as ScheduleConfig.on_days.
    days: List[int]
    hour: int
    minute: int
    timezone: str


CloudSchedule = Union[CloudIntervalSchedule, CloudDailySchedule, CloudWeeklySchedule]


class ScheduleSupported(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    supported: Literal[True] = True
    schedule: CloudSchedule


class ScheduleUnsupported(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    supported: Literal[False] = False
    reason: str


ScheduleMapping = Union[ScheduleSupported, ScheduleUnsupported]


@typechecked
def wire(sched: CloudSchedule) -> Dict[str, Any]:
    """The JSON body shape. Unset bounds are dropped rather than sent as null, which is what the
    cloud's schema expects and what keeps the definition fingerprint stable across versions."""
    return sched.model_dump(exclude_none=True)


@typechecked
def p_zone_name(name: str) -> str:
    """A concrete IANA name the cloud can hand to its own tz database. "local" and anything
    unresolvable fall back to this host's zone, which is what the local scheduler already does."""
    if not name or name == "local":
        return host_timezone_name()
    try:
        ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return host_timezone_name()
    return name


@typechecked
def p_epoch_ms(when: datetime) -> int:
    # Naive datetimes are host-local, matching how the local scheduler reads its own stored dates.
    aware = when if when.tzinfo is not None else when.replace(tzinfo=ZoneInfo(host_timezone_name()))
    return int(aware.timestamp() * 1000)


@typechecked
def p_bounds(sched: ScheduleConfig) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if sched.ends_at is not None:
        out["ends_at"] = p_epoch_ms(sched.ends_at)
    if sched.max_runs is not None:
        out["max_runs"] = sched.max_runs
    return out


@typechecked
def to_cloud_schedule(sched: ScheduleConfig) -> ScheduleMapping:
    bounds = p_bounds(sched)
    if sched.repeat_unit == "minute":
        return ScheduleSupported(schedule=CloudIntervalSchedule(minutes=max(5, sched.repeat_every), **bounds))
    if sched.repeat_unit == "hour":
        return ScheduleSupported(
            schedule=CloudIntervalSchedule(minutes=max(5, sched.repeat_every * 60), **bounds)
        )

    zone = p_zone_name(sched.timezone)
    if sched.repeat_unit == "day":
        if sched.repeat_every == 1:
            return ScheduleSupported(
                schedule=CloudDailySchedule(hour=sched.hour, minute=sched.minute, timezone=zone, **bounds)
            )
        return ScheduleUnsupported(
            reason=(
                f"{CADENCE_PREFIX} This one runs every {sched.repeat_every} days at a set time, "
                "which the cloud scheduler cannot do yet, so it stays on this device."
            ),
        )

    if sched.repeat_unit == "week":
        if not sched.on_days:
            return ScheduleUnsupported(
                reason="Pick the days this should run on before choosing where it runs.",
            )
        if sched.repeat_every == 1:
            return ScheduleSupported(
                schedule=CloudWeeklySchedule(
                    days=sorted(sched.on_days),
                    hour=sched.hour,
                    minute=sched.minute,
                    timezone=zone,
                    **bounds,
                )
            )
        return ScheduleUnsupported(
            reason=(
                f"{CADENCE_PREFIX} This one runs every {sched.repeat_every} weeks, "
                "which the cloud scheduler cannot do yet, so it stays on this device."
            ),
        )

    return ScheduleUnsupported(
        reason=(
            f"{CADENCE_PREFIX} This one runs monthly, "
            "which the cloud scheduler cannot do yet, so it stays on this device."
        ),
    )
