"""Tests for the iris fetch-daemon hang watchdog.

Covers the pure hang predicate (`_is_hung`) and harbor `updated_at` parsing
(`_parse_harbor_iso`) directly — no GCS / iris I/O. The I/O wrappers
(`_harbor_liveness`, `_watchdog_kill`) are thin subprocess shells exercised in
integration, not unit-mocked here.
"""

from datetime import datetime, timedelta, timezone

import pytest

from hpc.iris_fetch_daemon import _is_hung, _parse_harbor_iso

THRESHOLD = 7200  # 2h, the daemon default


def _now():
    return datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)


def test_hung_when_served_and_stale_past_threshold():
    stale = _now() - timedelta(hours=2, minutes=1)
    assert _is_hung(stale, n_completed=7110, now=_now(), threshold_seconds=THRESHOLD)


def test_not_hung_when_recently_flushed():
    fresh = _now() - timedelta(minutes=3)
    assert not _is_hung(
        fresh, n_completed=7110, now=_now(), threshold_seconds=THRESHOLD
    )


def test_not_hung_just_under_threshold():
    edge = _now() - timedelta(seconds=THRESHOLD - 1)
    assert not _is_hung(edge, n_completed=500, now=_now(), threshold_seconds=THRESHOLD)


@pytest.mark.parametrize("n_completed", [None, 0])
def test_cold_compile_never_hung(n_completed):
    # No trials served yet (cold compile): stale updated_at must NOT trip the
    # watchdog — that's the engine healthcheck's job, not ours.
    very_stale = _now() - timedelta(hours=10)
    assert not _is_hung(
        very_stale, n_completed=n_completed, now=_now(), threshold_seconds=THRESHOLD
    )


def test_no_result_json_never_hung():
    # _harbor_liveness returns (None, None) when result.json is absent.
    assert not _is_hung(None, n_completed=None, now=_now(), threshold_seconds=THRESHOLD)


def test_parse_harbor_iso_trailing_z():
    dt = _parse_harbor_iso("2026-06-04T02:08:24.015424Z")
    assert dt == datetime(2026, 6, 4, 2, 8, 24, 15424, tzinfo=timezone.utc)


def test_parse_harbor_iso_offset():
    dt = _parse_harbor_iso("2026-06-04T02:08:24+00:00")
    assert dt == datetime(2026, 6, 4, 2, 8, 24, tzinfo=timezone.utc)


def test_parse_harbor_iso_without_offset_assumes_utc():
    dt = _parse_harbor_iso("2026-06-04T02:08:24.015424")
    assert dt == datetime(2026, 6, 4, 2, 8, 24, 15424, tzinfo=timezone.utc)


@pytest.mark.parametrize("bad", ["", "not-a-date", None])
def test_parse_harbor_iso_garbage_returns_none(bad):
    assert _parse_harbor_iso(bad) is None
