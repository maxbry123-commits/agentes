"""Engine health: how many failures shut a frontend, and for how long.

Measured before this existed: once DuckDuckGo stopped answering TCP, three
consecutive 44-query rounds each paid its full 8s budget on EVERY query, so
keyless p50 went 1.0s -> 8.5s while Startpage still served 40/40.

The racing behaviour that keeps a dead engine off the critical path lives in
test_keyless_race.py; this file pins the state machine underneath it.
"""

import pytest

from backend.apps.web.tier_breaker import (
    FAILURES_TO_OPEN,
    FIRST_COOLDOWN_SECONDS,
    MAX_COOLDOWN_SECONDS,
    record_tier_failure,
    record_tier_success,
    reset_tier_health,
    tier_cooldown_left,
)


@pytest.fixture(autouse=True)
def p_clean():
    reset_tier_health()
    yield
    reset_tier_health()


def test_an_error_answer_takes_three_strikes():
    """A 202 or a 403 can be a bad minute, so one is not enough to shut an engine out."""
    for _ in range(FAILURES_TO_OPEN - 1):
        record_tier_failure("ddg")
    assert tier_cooldown_left("ddg") == 0.0
    record_tier_failure("ddg")
    assert 0 < tier_cooldown_left("ddg") <= FIRST_COOLDOWN_SECONDS


def test_silence_is_conclusive_on_the_first_failure():
    """A frontend returning nothing at all is not ambiguous, and making the user prove it
    three times is what put 8.8s on their first three searches after launch."""
    record_tier_failure("ddg", conclusive=True)
    assert 0 < tier_cooldown_left("ddg") <= FIRST_COOLDOWN_SECONDS


def test_success_clears_the_streak():
    for _ in range(FAILURES_TO_OPEN):
        record_tier_failure("ddg")
    assert tier_cooldown_left("ddg") > 0
    record_tier_success("ddg")
    assert tier_cooldown_left("ddg") == 0.0


def test_a_recovered_engine_is_not_blacklisted_forever():
    """The cooldown must expire on its own, or one bad afternoon costs us an engine for good."""
    record_tier_failure("ddg", now=0.0, conclusive=True)
    assert tier_cooldown_left("ddg", now=0.0) == pytest.approx(FIRST_COOLDOWN_SECONDS)
    assert tier_cooldown_left("ddg", now=FIRST_COOLDOWN_SECONDS + 1) == 0.0
    record_tier_success("ddg")
    for _ in range(FAILURES_TO_OPEN - 1):
        record_tier_failure("ddg")
    assert tier_cooldown_left("ddg") == 0.0, "a success must reset the streak, not just the clock"


def test_cooldown_doubles_and_is_capped():
    seen = []
    now = 0.0
    for _ in range(12):
        record_tier_failure("ddg", now=now, conclusive=True)
        seen.append(tier_cooldown_left("ddg", now=now))
        now += seen[-1] + 1
    assert seen[0] == pytest.approx(FIRST_COOLDOWN_SECONDS)
    assert seen[1] > seen[0]
    assert max(seen) <= MAX_COOLDOWN_SECONDS


def test_engines_are_tracked_independently():
    for _ in range(FAILURES_TO_OPEN):
        record_tier_failure("ddg")
    assert tier_cooldown_left("ddg") > 0
    assert tier_cooldown_left("startpage") == 0.0
