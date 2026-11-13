"""The free engines race; a dead one must not stand between the user and an answer.

The bug these pin is a cold-start bug, so it hides from any average taken over a
long-lived process. Measured on a fresh backend against a DuckDuckGo that had
stopped answering TCP: q1 8,812ms, q2 8,825ms, q3 8,934ms, then 585ms. Breaker
state is per-process and the desktop app starts a backend on every launch, so
every user's first three searches after opening the app paid full price to
rediscover what the last process already knew.
"""

import asyncio

import pytest

from backend.apps.web.keyless_race import KeylessEngine, race_keyless
from backend.apps.web.tier_breaker import (
    FIRST_COOLDOWN_SECONDS,
    reset_tier_health,
    tier_cooldown_left,
)


@pytest.fixture(autouse=True)
def p_clean():
    reset_tier_health()
    yield
    reset_tier_health()


def p_engine(name, fn):
    return KeylessEngine(name=name, run=fn)


def p_answers(name, after=0.0, calls=None):
    async def run():
        if calls is not None:
            calls.append(name)
        if after:
            await asyncio.sleep(after)
        return {"backend": name}
    return run


def p_silent(name, calls=None):
    async def run():
        if calls is not None:
            calls.append(name)
        await asyncio.sleep(30)
    return run


def p_raises(name, calls=None):
    async def run():
        if calls is not None:
            calls.append(name)
        raise RuntimeError(f"{name} served its bot challenge")
    return run


def p_empty(name, calls=None):
    async def run():
        if calls is not None:
            calls.append(name)
        return None
    return run


@pytest.mark.asyncio
async def test_healthy_leader_wins_alone_and_sends_no_extra_traffic():
    """The whole cost case for racing rests on this: a healthy engine must not double our requests."""
    calls = []
    out = await race_keyless(
        [p_engine("ddg", p_answers("ddg", 0.01, calls)),
         p_engine("startpage", p_answers("startpage", 0.01, calls))],
        budget=5.0, hedge_after=0.3,
    )
    assert out.result == {"backend": "ddg"}
    assert calls == ["ddg"], "the second engine must not be dispatched when the first is fast"


@pytest.mark.asyncio
async def test_a_silent_leader_costs_the_hedge_not_the_budget():
    """This is the cold-start fix: a blackholed engine used to cost its full 8s tier budget."""
    loop = asyncio.get_running_loop()
    t0 = loop.time()
    out = await race_keyless(
        [p_engine("ddg", p_silent("ddg")),
         p_engine("startpage", p_answers("startpage", 0.01))],
        budget=5.0, hedge_after=0.3,
    )
    elapsed = loop.time() - t0
    assert out.result == {"backend": "startpage"}
    assert elapsed < 1.0, f"a dead leader should cost about the hedge delay, took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_a_fast_failure_starts_the_next_engine_immediately():
    """An engine that refuses outright should not make us wait out the hedge as well."""
    loop = asyncio.get_running_loop()
    t0 = loop.time()
    out = await race_keyless(
        [p_engine("ddg", p_raises("ddg")),
         p_engine("startpage", p_answers("startpage", 0.01))],
        budget=5.0, hedge_after=2.0,
    )
    assert out.result == {"backend": "startpage"}
    assert loop.time() - t0 < 1.0
    assert any("bot challenge" in e for e in out.errors)


@pytest.mark.asyncio
async def test_silence_shuts_the_engine_after_one_query():
    """One conclusive silence, not three, so the tax is one slow search rather than three."""
    await race_keyless(
        [p_engine("ddg", p_silent("ddg")),
         p_engine("startpage", p_answers("startpage", 0.01))],
        budget=5.0, hedge_after=0.3,
    )
    assert tier_cooldown_left("ddg") > 0
    assert tier_cooldown_left("startpage") == 0.0


@pytest.mark.asyncio
async def test_a_cooling_engine_is_not_dispatched_at_all():
    calls = []
    for _ in range(2):
        await race_keyless(
            [p_engine("ddg", p_silent("ddg", calls)),
             p_engine("startpage", p_answers("startpage", 0.01, calls))],
            budget=5.0, hedge_after=0.3,
        )
    assert calls.count("ddg") == 1, "the second query must not re-probe a conclusively dead engine"
    out = await race_keyless(
        [p_engine("ddg", p_silent("ddg", calls)),
         p_engine("startpage", p_answers("startpage", 0.01, calls))],
        budget=5.0, hedge_after=0.3,
    )
    assert any("skipped, still failing" in e for e in out.errors)


@pytest.mark.asyncio
async def test_a_recovered_engine_is_used_again(monkeypatch):
    """The fix must not quietly blacklist an engine that comes back."""
    import backend.apps.web.tier_breaker as TB
    calls = []
    await race_keyless(
        [p_engine("ddg", p_silent("ddg", calls)),
         p_engine("startpage", p_answers("startpage", 0.01, calls))],
        budget=5.0, hedge_after=0.3,
    )
    assert tier_cooldown_left("ddg") > 0

    # Jump past the cooldown rather than sleep through it.
    real_monotonic = TB.time.monotonic
    monkeypatch.setattr(TB.time, "monotonic",
                        lambda: real_monotonic() + FIRST_COOLDOWN_SECONDS + 1)
    calls.clear()
    out = await race_keyless(
        [p_engine("ddg", p_answers("ddg", 0.01, calls)),
         p_engine("startpage", p_answers("startpage", 0.01, calls))],
        budget=5.0, hedge_after=0.3,
    )
    assert out.result == {"backend": "ddg"}, "a healthy engine must be used again after the cooldown"
    assert tier_cooldown_left("ddg") == 0.0


@pytest.mark.asyncio
async def test_both_empty_reports_no_hits_not_a_failure():
    """A nonsense query must not slowly cool down two perfectly healthy engines."""
    for _ in range(5):
        out = await race_keyless(
            [p_engine("ddg", p_empty("ddg")), p_engine("startpage", p_empty("startpage"))],
            budget=5.0, hedge_after=0.3,
        )
        assert out.result is None
    assert tier_cooldown_left("ddg") == 0.0
    assert tier_cooldown_left("startpage") == 0.0


@pytest.mark.asyncio
async def test_an_empty_leader_still_lets_the_other_answer():
    out = await race_keyless(
        [p_engine("ddg", p_empty("ddg")),
         p_engine("startpage", p_answers("startpage", 0.01))],
        budget=5.0, hedge_after=2.0,
    )
    assert out.result == {"backend": "startpage"}


@pytest.mark.asyncio
async def test_every_engine_closed_returns_honestly():
    out = await race_keyless(
        [p_engine("ddg", p_raises("ddg")), p_engine("startpage", p_raises("startpage"))],
        budget=5.0, hedge_after=0.3,
    )
    assert out.result is None
    assert len(out.errors) == 2


@pytest.mark.asyncio
async def test_budget_bounds_the_whole_race():
    loop = asyncio.get_running_loop()
    t0 = loop.time()
    out = await race_keyless(
        [p_engine("ddg", p_silent("ddg")), p_engine("startpage", p_silent("startpage"))],
        budget=0.6, hedge_after=0.2,
    )
    assert out.result is None
    assert loop.time() - t0 < 2.0


@pytest.mark.asyncio
async def test_losing_engines_do_not_outlive_the_race():
    """A cancelled request must not keep running and surprise the user's network later."""
    live = {"n": 0}

    async def clingy():
        live["n"] += 1
        try:
            await asyncio.sleep(30)
        finally:
            live["n"] -= 1

    await race_keyless(
        [p_engine("ddg", clingy), p_engine("startpage", p_answers("startpage", 0.01))],
        budget=5.0, hedge_after=0.2,
    )
    assert live["n"] == 0
