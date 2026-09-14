"""Kalender-Tools fuer Cognithor: ICS-basiert mit optionalem CalDAV.

Ermoeglicht dem Agenten Kalender-Verwaltung ueber lokale ICS-Dateien
und optional ueber CalDAV-Server.

Tools:
  - calendar_today: Heutige Termine anzeigen
  - calendar_upcoming: Kommende Termine anzeigen
  - calendar_create_event: Neuen Termin erstellen
  - calendar_check_availability: Freie Zeitfenster finden

ICS-Parsing:
  - Primaer: ``icalendar``-Bibliothek (optional)
  - Fallback: Manueller VEVENT-Parser (kein externes Dependency)
  - Basis-RRULE-Support (DAILY, WEEKLY, MONTHLY)

Bibel-Referenz: §5.3 (jarvis-calendar Server)
"""

from __future__ import annotations

import asyncio
import contextlib
import re
import uuid
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cognithor.i18n import t
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Generator

    from cognithor.config import CognithorConfig

log = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────

_DEFAULT_EVENT_DURATION = timedelta(hours=1)
_MAX_UPCOMING_DAYS = 90
_MAX_RECURRENCE_INSTANCES = 365  # Maximale Instanzen für wiederkehrende Termine
_ICS_HEADER = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Jarvis Agent OS//Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""
_ICS_FOOTER = "END:VCALENDAR\n"

__all__ = [
    "CalendarError",
    "CalendarTools",
    "register_calendar_tools",
]


class CalendarError(Exception):
    """Fehler bei Kalender-Operationen."""


def _get_local_timezone() -> timezone:
    """Gibt die lokale Systemzeitzone zurueck."""
    try:
        import time as _time

        # On Windows tzname can be weird; fall back to UTC offset
        local_offset = timedelta(seconds=-_time.timezone)
        if _time.daylight and _time.altzone:
            local_offset = timedelta(seconds=-_time.altzone)
        return timezone(local_offset)
    except Exception:
        return UTC


def _get_configured_timezone(tz_str: str) -> timezone:
    """Parst eine Zeitzone aus Config-String."""
    if not tz_str:
        return _get_local_timezone()

    # Try zoneinfo (Python 3.9+)
    try:
        from zoneinfo import ZoneInfo

        zi = ZoneInfo(tz_str)
        # Convert to fixed offset for comparisons
        now = datetime.now(zi)
        return timezone(now.utcoffset() or timedelta(0))
    except Exception:
        log.debug("calendar_zoneinfo_parse_failed", exc_info=True)

    # Try UTC+N format
    match = re.match(r"UTC([+-])(\d{1,2})(?::(\d{2}))?", tz_str)
    if match:
        sign = 1 if match.group(1) == "+" else -1
        hours = int(match.group(2))
        minutes = int(match.group(3)) if match.group(3) else 0
        return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

    return _get_local_timezone()


def _parse_ics_datetime(value: str) -> datetime:
    """Parst ein ICS-Datum/Zeitformat.

    Unterstuetzt:
      - 20240115T103000Z (UTC)
      - 20240115T103000 (lokal)
      - 20240115 (ganztaegig)
      - Mit TZID-Prefix
    """
    # Remove TZID prefix if present
    if ":" in value:
        value = value.split(":")[-1]
    value = value.strip()

    if len(value) == 8:
        # Date only (all-day event)
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=_get_local_timezone())

    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)

    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=_get_local_timezone())
    except ValueError as err:
        raise CalendarError(f"Ungültiges Datumsformat: {value}") from err


def _format_ics_datetime(dt: datetime) -> str:
    """Formatiert eine datetime als ICS-String."""
    if dt.tzinfo == UTC:
        return dt.strftime("%Y%m%dT%H%M%SZ")
    return dt.strftime("%Y%m%dT%H%M%S")


def _format_ics_date(d: date) -> str:
    """Formatiert ein date als ICS-Datumstring."""
    return d.strftime("%Y%m%d")


class _VEvent:
    """Interner Repraesentant eines Kalender-Events."""

    __slots__ = (
        "all_day",
        "description",
        "dtend",
        "dtstart",
        "location",
        "rrule",
        "summary",
        "uid",
    )

    def __init__(
        self,
        uid: str = "",
        summary: str = "",
        dtstart: datetime | None = None,
        dtend: datetime | None = None,
        location: str = "",
        description: str = "",
        all_day: bool = False,
        rrule: str = "",
    ):
        self.uid = uid
        self.summary = summary
        self.dtstart = dtstart
        self.dtend = dtend
        self.location = location
        self.description = description
        self.all_day = all_day
        self.rrule = rrule

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert in ein Ausgabe-Dict."""
        return {
            "title": self.summary,
            "start": self.dtstart.isoformat() if self.dtstart else "",
            "end": self.dtend.isoformat() if self.dtend else "",
            "location": self.location,
            "description": self.description,
            "all_day": self.all_day,
        }

    def to_ics_block(self) -> str:
        """Generiert einen VEVENT-Block im ICS-Format."""
        lines = ["BEGIN:VEVENT"]
        lines.append(f"UID:{self.uid}")
        lines.append(f"DTSTAMP:{_format_ics_datetime(datetime.now(UTC))}")

        if self.all_day and self.dtstart:
            lines.append(f"DTSTART;VALUE=DATE:{_format_ics_date(self.dtstart.date())}")
            if self.dtend:
                lines.append(f"DTEND;VALUE=DATE:{_format_ics_date(self.dtend.date())}")
        else:
            if self.dtstart:
                lines.append(f"DTSTART:{_format_ics_datetime(self.dtstart)}")
            if self.dtend:
                lines.append(f"DTEND:{_format_ics_datetime(self.dtend)}")

        lines.append(f"SUMMARY:{self.summary}")
        if self.location:
            lines.append(f"LOCATION:{self.location}")
        if self.description:
            # Escape newlines for ICS
            desc_escaped = self.description.replace("\n", "\\n")
            lines.append(f"DESCRIPTION:{desc_escaped}")
        if self.rrule:
            lines.append(f"RRULE:{self.rrule}")

        lines.append("END:VEVENT")
        return "\n".join(lines)


def _parse_rrule_instances(
    event: _VEvent,
    range_start: datetime,
    range_end: datetime,
) -> Generator[_VEvent, None, None]:
    """Generiert Instanzen eines wiederkehrenden Events innerhalb eines Zeitraums.

    Unterstuetzt: FREQ=DAILY, WEEKLY, MONTHLY mit optionalem COUNT und UNTIL.
    """
    if not event.rrule or not event.dtstart:
        if event.dtstart and range_start <= event.dtstart <= range_end:
            yield event
        return

    rrule = event.rrule.upper()

    # Extract FREQ
    freq_match = re.search(r"FREQ=(DAILY|WEEKLY|MONTHLY|YEARLY)", rrule)
    if not freq_match:
        if event.dtstart and range_start <= event.dtstart <= range_end:
            yield event
        return

    freq = freq_match.group(1)

    # Extract INTERVAL
    interval_match = re.search(r"INTERVAL=(\d+)", rrule)
    interval = int(interval_match.group(1)) if interval_match else 1

    # Extract COUNT
    count_match = re.search(r"COUNT=(\d+)", rrule)
    max_count = int(count_match.group(1)) if count_match else _MAX_RECURRENCE_INSTANCES

    # Extract UNTIL
    until_match = re.search(r"UNTIL=(\d{8}(?:T\d{6}Z?)?)", rrule)
    until = _parse_ics_datetime(until_match.group(1)) if until_match else range_end

    duration = (event.dtend - event.dtstart) if event.dtend else _DEFAULT_EVENT_DURATION
    current = event.dtstart
    count = 0

    while current <= min(until, range_end) and count < max_count:
        if current >= range_start:
            instance = _VEvent(
                uid=event.uid,
                summary=event.summary,
                dtstart=current,
                dtend=current + duration,
                location=event.location,
                description=event.description,
                all_day=event.all_day,
            )
            yield instance

        count += 1
        if freq == "DAILY":
            current = current + timedelta(days=interval)
        elif freq == "WEEKLY":
            current = current + timedelta(weeks=interval)
        elif freq == "MONTHLY":
            # Next month, same day
            month = current.month + interval
            year = current.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            try:
                current = current.replace(year=year, month=month)
            except ValueError:
                # Day does not exist (e.g. Feb 31)
                break
        elif freq == "YEARLY":
            try:
                current = current.replace(year=current.year + interval)
            except ValueError:
                break


def _parse_ics_manual(content: str) -> list[_VEvent]:
    """Manueller ICS-Parser als Fallback (kein icalendar-Dependency).

    Parst BEGIN:VEVENT...END:VEVENT Bloecke.
    """
    events: list[_VEvent] = []
    in_event = False
    event_lines: list[str] = []

    for line in content.splitlines():
        line = line.rstrip()
        if line == "BEGIN:VEVENT":
            in_event = True
            event_lines = []
        elif line == "END:VEVENT" and in_event:
            in_event = False
            event = _parse_vevent_block(event_lines)
            if event:
                events.append(event)
        elif in_event:
            # Unfold: lines starting with space/tab belong to the previous line
            if line.startswith((" ", "\t")) and event_lines:
                event_lines[-1] += line[1:]
            else:
                event_lines.append(line)

    return events


def _parse_vevent_block(lines: list[str]) -> _VEvent | None:
    """Parst die Zeilen eines VEVENT-Blocks in ein _VEvent-Objekt."""
    props: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        # Property name without parameters (e.g. DTSTART;TZID=Europe/Berlin → DTSTART)
        prop_name = key.split(";")[0].upper()
        props[prop_name] = value.strip()

    if "DTSTART" not in props:
        return None

    uid = props.get("UID", str(uuid.uuid4()))
    summary = props.get("SUMMARY", "(kein Titel)")
    location = props.get("LOCATION", "")
    description = props.get("DESCRIPTION", "").replace("\\n", "\n")
    rrule = props.get("RRULE", "")

    try:
        dtstart = _parse_ics_datetime(props["DTSTART"])
    except (CalendarError, ValueError):
        return None

    dtend = None
    if "DTEND" in props:
        with contextlib.suppress(CalendarError, ValueError):
            dtend = _parse_ics_datetime(props["DTEND"])

    # All-day detection: no T in DTSTART or VALUE=DATE
    all_day = "T" not in props.get("DTSTART", "T")
    # Also check the key line for VALUE=DATE
    for line in lines:
        if line.upper().startswith("DTSTART") and "VALUE=DATE" in line.upper():
            all_day = True
            break

    if dtend is None and not all_day:
        dtend = dtstart + _DEFAULT_EVENT_DURATION

    return _VEvent(
        uid=uid,
        summary=summary,
        dtstart=dtstart,
        dtend=dtend,
        location=location,
        description=description,
        all_day=all_day,
        rrule=rrule,
    )


def _parse_ics_with_library(content: str) -> list[_VEvent]:
    """Parst ICS-Inhalt mit der icalendar-Bibliothek."""
    try:
        from icalendar import Calendar  # type: ignore[import-untyped]
    except ImportError:
        return _parse_ics_manual(content)

    try:
        cal = Calendar.from_ical(content)
    except Exception:
        return _parse_ics_manual(content)

    events: list[_VEvent] = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        dtstart_val = component.get("dtstart")
        if dtstart_val is None:
            continue

        dtstart_dt = dtstart_val.dt
        all_day = isinstance(dtstart_dt, date) and not isinstance(dtstart_dt, datetime)

        if all_day:
            dtstart = datetime.combine(dtstart_dt, time.min).replace(tzinfo=_get_local_timezone())
        elif dtstart_dt.tzinfo is None:
            dtstart = dtstart_dt.replace(tzinfo=_get_local_timezone())
        else:
            dtstart = dtstart_dt

        dtend = None
        dtend_val = component.get("dtend")
        if dtend_val is not None:
            dtend_dt = dtend_val.dt
            if isinstance(dtend_dt, date) and not isinstance(dtend_dt, datetime):
                dtend = datetime.combine(dtend_dt, time.min).replace(tzinfo=_get_local_timezone())
            elif dtend_dt.tzinfo is None:
                dtend = dtend_dt.replace(tzinfo=_get_local_timezone())
            else:
                dtend = dtend_dt

        if dtend is None and not all_day:
            dtend = dtstart + _DEFAULT_EVENT_DURATION

        rrule = ""
        rrule_val = component.get("rrule")
        if rrule_val:
            rrule = rrule_val.to_ical().decode("utf-8")

        events.append(
            _VEvent(
                uid=str(component.get("uid", uuid.uuid4())),
                summary=str(component.get("summary", "(kein Titel)")),
                dtstart=dtstart,
                dtend=dtend,
                location=str(component.get("location", "")),
                description=str(component.get("description", "")).replace("\\n", "\n"),
                all_day=all_day,
                rrule=rrule,
            )
        )

    return events


class CalendarTools:
    """Kalender-Operationen ueber lokale ICS-Dateien. [B§5.3]

    Attributes:
        _ics_path: Pfad zur lokalen ICS-Datei.
        _tz: Konfigurierte Zeitzone.
    """

    def __init__(self, config: CognithorConfig) -> None:
        """Initialisiert CalendarTools.

        Args:
            config: Jarvis-Konfiguration mit calendar-Sektion.
        """
        self._config = config
        cal_cfg = config.calendar

        ics_path_str = cal_cfg.ics_path
        if ics_path_str:
            self._ics_path = Path(ics_path_str).expanduser().resolve()
        else:
            self._ics_path = Path(config.cognithor_home) / "calendar.ics"

        self._tz = _get_configured_timezone(cal_cfg.timezone)

        # CalDAV client (optional)
        self._caldav_client: Any = None
        self._caldav_url = cal_cfg.caldav_url
        self._caldav_username = cal_cfg.username
        self._caldav_password_env = cal_cfg.password_env

        # Create ICS file if not present
        self._ensure_ics_file()

    def _ensure_ics_file(self) -> None:
        """Erstellt die ICS-Datei falls nicht vorhanden."""
        if not self._ics_path.exists():
            self._ics_path.parent.mkdir(parents=True, exist_ok=True)
            self._ics_path.write_text(_ICS_HEADER + _ICS_FOOTER, encoding="utf-8")
            log.info("calendar_ics_created", path=str(self._ics_path))

    def _read_events(self) -> list[_VEvent]:
        """Liest alle Events aus der ICS-Datei."""
        if not self._ics_path.exists():
            return []

        content = self._ics_path.read_text(encoding="utf-8")
        if not content.strip():
            return []

        # Try icalendar library, fall back to manual parser
        return _parse_ics_with_library(content)

    def _get_events_in_range(
        self,
        range_start: datetime,
        range_end: datetime,
    ) -> list[_VEvent]:
        """Gibt alle Events in einem Zeitraum zurueck (inkl. Wiederholungen)."""
        raw_events = self._read_events()
        result: list[_VEvent] = []

        for event in raw_events:
            if event.rrule:
                for instance in _parse_rrule_instances(event, range_start, range_end):
                    result.append(instance)
            elif event.dtstart and range_start <= event.dtstart <= range_end:
                result.append(event)
            elif (
                event.dtstart
                and event.dtend
                and event.dtstart <= range_end
                and event.dtend >= range_start
            ):
                # Event spans the time range
                result.append(event)

        result.sort(key=lambda e: e.dtstart or datetime.min.replace(tzinfo=UTC))
        return result

    def _append_event(self, event: _VEvent) -> None:
        """Fuegt ein Event zur ICS-Datei hinzu."""
        content = ""
        if self._ics_path.exists():
            content = self._ics_path.read_text(encoding="utf-8")

        if not content.strip():
            content = _ICS_HEADER + _ICS_FOOTER

        # Insert event before END:VCALENDAR
        vevent_block = event.to_ics_block()
        content = content.replace(
            "END:VCALENDAR",
            vevent_block + "\nEND:VCALENDAR",
        )

        self._ics_path.write_text(content, encoding="utf-8")

    def _now(self) -> datetime:
        """Aktuelle Zeit in konfigurierter Zeitzone."""
        return datetime.now(self._tz)

    async def calendar_today(self, date: str = "") -> str:
        """Zeigt die heutigen Termine an.

        Args:
            date: Optionales Datum im ISO-Format (Default: heute).

        Returns:
            Formatierte Terminliste.
        """
        if date:
            try:
                target = datetime.fromisoformat(date)
                if target.tzinfo is None:
                    target = target.replace(tzinfo=self._tz)
            except ValueError as err:
                raise CalendarError(f"Ungültiges Datum: {date} (erwartet: YYYY-MM-DD)") from err
        else:
            target = self._now()

        day_start = datetime.combine(target.date(), time.min).replace(tzinfo=self._tz)
        day_end = datetime.combine(target.date(), time(23, 59, 59)).replace(tzinfo=self._tz)

        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, self._get_events_in_range, day_start, day_end)

        date_str = target.strftime("%A, %d.%m.%Y")
        if not events:
            return f"Keine Termine am {date_str}."

        return _format_events(events, f"Termine am {date_str}")

    async def calendar_upcoming(self, days: int = 7) -> str:
        """Zeigt kommende Termine an.

        Args:
            days: Anzahl Tage vorausschauen (1-90, Default: 7).

        Returns:
            Formatierte Terminliste sortiert nach Startzeit.
        """
        days = max(1, min(days, _MAX_UPCOMING_DAYS))
        now = self._now()
        range_end = now + timedelta(days=days)

        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, self._get_events_in_range, now, range_end)

        if not events:
            return f"Keine Termine in den nächsten {days} Tagen."

        return _format_events(events, f"Termine der nächsten {days} Tage")

    async def calendar_create_event(
        self,
        title: str = "",
        start: str = "",
        end: str = "",
        location: str = "",
        description: str = "",
        all_day: bool = False,
    ) -> str:
        """Erstellt einen neuen Termin.

        Args:
            title: Titel des Termins (erforderlich).
            start: Startzeit im ISO-Format (erforderlich, z.B. 2024-01-15T10:00:00).
            end: Endzeit im ISO-Format (optional, Default: Start + 1h).
            location: Ort (optional).
            description: Beschreibung (optional).
            all_day: Ganztaegig (Default: False).

        Returns:
            Bestaetigungsnachricht.
        """
        if not title:
            raise CalendarError(t("calendar.no_title"))

        if not start:
            raise CalendarError(t("calendar.no_start_time"))

        try:
            dtstart = datetime.fromisoformat(start)
            if dtstart.tzinfo is None:
                dtstart = dtstart.replace(tzinfo=self._tz)
        except ValueError as err:
            raise CalendarError(
                f"Ungültige Startzeit: {start} (erwartet: ISO-Format, z.B. 2024-01-15T10:00:00)"
            ) from err

        dtend = None
        if end:
            try:
                dtend = datetime.fromisoformat(end)
                if dtend.tzinfo is None:
                    dtend = dtend.replace(tzinfo=self._tz)
            except ValueError as err:
                raise CalendarError(f"Ungültige Endzeit: {end} (erwartet: ISO-Format)") from err
        elif not all_day:
            dtend = dtstart + _DEFAULT_EVENT_DURATION

        event = _VEvent(
            uid=str(uuid.uuid4()),
            summary=title,
            dtstart=dtstart,
            dtend=dtend,
            location=location,
            description=description,
            all_day=all_day,
        )

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._append_event, event)

        log.info("calendar_event_created", title=title, start=start)

        start_str = (
            dtstart.strftime("%d.%m.%Y %H:%M") if not all_day else dtstart.strftime("%d.%m.%Y")
        )
        result = f"Termin erstellt: {title}\nDatum: {start_str}"
        if dtend and not all_day:
            result += f" - {dtend.strftime('%H:%M')}"
        if location:
            result += f"\nOrt: {location}"
        return result

    async def calendar_check_availability(
        self,
        date: str = "",
        duration_minutes: int = 60,
        work_hours_start: str = "09:00",
        work_hours_end: str = "17:00",
    ) -> str:
        """Findet freie Zeitfenster innerhalb der Arbeitszeit.

        Args:
            date: Datum im ISO-Format (Default: heute).
            duration_minutes: Gewuenschte Dauer in Minuten (Default: 60).
            work_hours_start: Beginn der Arbeitszeit (Default: 09:00).
            work_hours_end: Ende der Arbeitszeit (Default: 17:00).

        Returns:
            Liste freier Zeitfenster.
        """
        if date:
            try:
                target = datetime.fromisoformat(date)
                if target.tzinfo is None:
                    target = target.replace(tzinfo=self._tz)
            except ValueError as err:
                raise CalendarError(f"Ungültiges Datum: {date} (erwartet: YYYY-MM-DD)") from err
        else:
            target = self._now()

        # Parse work hours
        try:
            wh_start = time.fromisoformat(work_hours_start)
            wh_end = time.fromisoformat(work_hours_end)
        except ValueError as err:
            raise CalendarError(
                f"Ungültige Arbeitszeit: {work_hours_start}-{work_hours_end} (erwartet: HH:MM)"
            ) from err

        day_start = datetime.combine(target.date(), wh_start).replace(tzinfo=self._tz)
        day_end = datetime.combine(target.date(), wh_end).replace(tzinfo=self._tz)

        if day_start >= day_end:
            raise CalendarError("Arbeitszeit-Ende muss nach dem Start liegen.")

        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(None, self._get_events_in_range, day_start, day_end)

        # Collect busy time slots (sorted)
        busy: list[tuple[datetime, datetime]] = []
        for event in events:
            if event.all_day:
                # All-day events block the entire day
                busy.append((day_start, day_end))
            elif event.dtstart and event.dtend:
                ev_start = max(event.dtstart, day_start)
                ev_end = min(event.dtend, day_end)
                if ev_start < ev_end:
                    busy.append((ev_start, ev_end))

        # Merge overlapping busy time slots
        busy.sort(key=lambda x: x[0])
        merged: list[tuple[datetime, datetime]] = []
        for start_t, end_t in busy:
            if merged and start_t <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end_t))
            else:
                merged.append((start_t, end_t))

        # Calculate free time slots
        desired_duration = timedelta(minutes=duration_minutes)
        free_slots: list[tuple[datetime, datetime]] = []
        current = day_start

        for busy_start, busy_end in merged:
            if busy_start > current:
                gap = busy_start - current
                if gap >= desired_duration:
                    free_slots.append((current, busy_start))
            current = max(current, busy_end)

        # Last slot until end of work hours
        if day_end > current:
            gap = day_end - current
            if gap >= desired_duration:
                free_slots.append((current, day_end))

        # Format output
        date_str = target.strftime("%d.%m.%Y")
        header = (
            f"Verfügbarkeit am {date_str} "
            f"({work_hours_start}-{work_hours_end}, "
            f"min. {duration_minutes} Min.)"
        )
        lines = [header, "=" * len(header), ""]

        if not free_slots:
            lines.append("Keine freien Zeitfenster gefunden.")
            if merged:
                lines.append("")
                lines.append("Belegte Zeiten:")
                for b_start, b_end in merged:
                    lines.append(f"  {b_start.strftime('%H:%M')} - {b_end.strftime('%H:%M')}")
        else:
            lines.append(f"Freie Zeitfenster ({len(free_slots)}):")
            for slot_start, slot_end in free_slots:
                slot_duration = int((slot_end - slot_start).total_seconds() / 60)
                lines.append(
                    f"  {slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')} "
                    f"({slot_duration} Min.)"
                )

            if events:
                lines.extend(["", f"Bestehende Termine ({len(events)}):"])
                for event in events:
                    if event.dtstart:
                        time_str = "ganztägig" if event.all_day else event.dtstart.strftime("%H:%M")
                        end_str = (
                            ""
                            if event.all_day or not event.dtend
                            else f"-{event.dtend.strftime('%H:%M')}"
                        )
                        lines.append(f"  {time_str}{end_str}: {event.summary}")

        return "\n".join(lines)


def _format_events(events: list[_VEvent], title: str) -> str:
    """Formatiert eine Event-Liste fuer die Ausgabe."""
    lines = [title, "=" * len(title), ""]

    for event in events:
        if event.all_day:
            time_str = "ganztägig"
        elif event.dtstart:
            time_str = event.dtstart.strftime("%H:%M")
            if event.dtend:
                time_str += f" - {event.dtend.strftime('%H:%M')}"
        else:
            time_str = ""

        date_str = event.dtstart.strftime("%d.%m.%Y") if event.dtstart else ""

        lines.append(f"[{date_str}] {time_str}")
        lines.append(f"  Titel: {event.summary}")
        if event.location:
            lines.append(f"  Ort: {event.location}")
        if event.description:
            desc_preview = event.description[:200]
            if len(event.description) > 200:
                desc_preview += "..."
            lines.append(f"  Beschreibung: {desc_preview}")
        lines.append("")

    return "\n".join(lines)


def register_calendar_tools(
    mcp_client: Any,
    config: CognithorConfig,
) -> CalendarTools | None:
    """Registriert Kalender-Tools beim MCP-Client.

    Registriert mit lokalem ICS-Fallback, auch wenn CalDAV nicht konfiguriert ist.
    Registriert nur wenn calendar.enabled=True.

    Args:
        mcp_client: JarvisMCPClient-Instanz.
        config: CognithorConfig mit calendar-Sektion.

    Returns:
        CalendarTools-Instanz oder None wenn deaktiviert.
    """
    cal_cfg = getattr(config, "calendar", None)
    if cal_cfg is None or not cal_cfg.enabled:
        log.debug("calendar_tools_disabled")
        return None

    cal = CalendarTools(config)

    mcp_client.register_builtin_handler(
        "calendar_today",
        cal.calendar_today,
        description=("Zeigt die heutigen Kalender-Termine an. Optional ein anderes Datum angeben."),
        input_schema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Datum im ISO-Format (Default: heute, z.B. 2024-01-15)",
                    "default": "",
                },
            },
        },
    )

    mcp_client.register_builtin_handler(
        "calendar_upcoming",
        cal.calendar_upcoming,
        description=("Zeigt kommende Kalender-Termine an, sortiert nach Startzeit."),
        input_schema={
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Anzahl Tage vorausschauen (1-90, Default: 7)",
                    "default": 7,
                },
            },
        },
    )

    mcp_client.register_builtin_handler(
        "calendar_create_event",
        cal.calendar_create_event,
        description=("Neuen Kalender-Termin erstellen. Schreibt in die lokale ICS-Datei."),
        input_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titel des Termins",
                },
                "start": {
                    "type": "string",
                    "description": "Startzeit im ISO-Format (z.B. 2024-01-15T10:00:00)",
                },
                "end": {
                    "type": "string",
                    "description": "Endzeit im ISO-Format (optional, Default: Start + 1h)",
                    "default": "",
                },
                "location": {
                    "type": "string",
                    "description": "Ort des Termins",
                    "default": "",
                },
                "description": {
                    "type": "string",
                    "description": "Beschreibung",
                    "default": "",
                },
                "all_day": {
                    "type": "boolean",
                    "description": "Ganztägiger Termin",
                    "default": False,
                },
            },
            "required": ["title", "start"],
        },
    )

    mcp_client.register_builtin_handler(
        "calendar_check_availability",
        cal.calendar_check_availability,
        description=(
            "Freie Zeitfenster innerhalb der Arbeitszeit finden. Berücksichtigt bestehende Termine."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Datum im ISO-Format (Default: heute)",
                    "default": "",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Gewünschte Dauer in Minuten (Default: 60)",
                    "default": 60,
                },
                "work_hours_start": {
                    "type": "string",
                    "description": "Beginn der Arbeitszeit (Default: 09:00)",
                    "default": "09:00",
                },
                "work_hours_end": {
                    "type": "string",
                    "description": "Ende der Arbeitszeit (Default: 17:00)",
                    "default": "17:00",
                },
            },
        },
    )

    log.info(
        "calendar_tools_registered",
        tools=[
            "calendar_today",
            "calendar_upcoming",
            "calendar_create_event",
            "calendar_check_availability",
        ],
    )
    return cal
